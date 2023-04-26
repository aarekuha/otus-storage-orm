import redis
import logging

from .redis_item import RedisItem
from .redis_item import T as SubclassItemType
from ..operation_result import OperationResult
from ..operation_result import OperationStatus

from ..storage_orm import StorageORM


class RedisORM(StorageORM):
    """ Работа с БД Redis через объектное представление """
    _pipe: redis.client.Pipeline
    _client: redis.Redis

    def __init__(
        self,
        client: redis.Redis = None,
        host: str = None,
        port: int = 6379,
        db: int = 0,
    ) -> None:
        if client:
            self._client = client
        elif host:
            self._client = redis.Redis(host=host, port=port, db=db)
        else:
            raise Exception(f"StorageORM-init must contains redis_client or host values...")

        self._pipe = self._client.pipeline()
        if not RedisItem._db_instance:
            RedisItem._set_global_instance(db_instance=self._client)

    def save(self, item: RedisItem) -> OperationResult:
        """ Одиночная вставка """
        return item.save()

    def bulk_create(self, items: list[SubclassItemType]) -> OperationResult:
        """ Групповая вставка """
        try:
            for redis_item in items:
                self._pipe.mset(mapping=redis_item.mapping)
            self._pipe.execute()
            return OperationResult(status=OperationStatus.success)
        except Exception as exception:
            self._on_error_actions(exception=exception)
            return OperationResult(
                status=OperationStatus.failed,
                message=str(exception),
            )

    def _on_error_actions(self, exception: Exception) -> None:
        """
            Действия, выполняющиеся в случае возникновения исключения
                во время вставки, сохранения, получения данных из БД
        """
        logging.exception(exception)
