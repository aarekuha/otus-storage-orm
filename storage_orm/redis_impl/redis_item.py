from __future__ import annotations
import re
import copy
import redis
import itertools
from typing import Any
from typing import cast
from typing import Union
from typing import Mapping
from typing import Type
from typing import TypeVar

from ..storage_item import StorageItem
from ..operation_result import OperationResult
from ..operation_result import OperationStatus

from ..exceptions import NotFoundException
from ..exceptions import MoreThanOneFoundException

# Redis: переопределения типов для корректной работы линтеров
_Value = Union[bytes, float, int, str]
_Key = Union[str, bytes]
ResponseT = Any

T = TypeVar('T', bound='RedisItem')
IN_PREFIX = "__in"
KEYS_DELIMITER = "."


class RedisItem(StorageItem):
    _table: str
    _table_keys: dict[str, int]
    _params: Mapping[_Key, _Value]
    _db_instance: Union[redis.Redis, None] = None

    class Meta:
        table = ""  # Pattern имени записи, например, "subsystem.{subsystem_id}.tag.{tag_id}"

    def __init_subclass__(cls) -> None:
        cls._table_keys = {
            index.replace("{", "").replace("}", ""): key
                for key, index in enumerate(cls.Meta.table.split(KEYS_DELIMITER))
                    if index.startswith("{") and index.endswith("}")
        }

    @classmethod
    def _make_kwargs_from_objects(cls: Type[T], objects: list[T]) -> dict:
        """
            Конкатенация атрибутов объектов и их подготовка для
                использования в качестве фильтров
        """
        result_kwargs: dict = {}
        for obj in objects:
            for key, position in obj._table_keys.items():
                value: str = obj._table.split(KEYS_DELIMITER)[position]
                if key in result_kwargs:
                    result_kwargs[key] += str(value)
                else:
                    result_kwargs[key] = str(value)

        for key in result_kwargs.keys():
            result_kwargs[key] = f"[{result_kwargs[key]}]"

        print(f"{result_kwargs=}")

        return result_kwargs

    def __init__(self, **kwargs) -> None:
        # Формирование полей модели из переданных дочернему классу аргументов
        [self.__dict__.__setitem__(key, value) for key, value in kwargs.items()]
        # Формирование изолированной среды с данными класса для дальнейшей работы с БД
        self._table = self.__class__.Meta.table.format(**kwargs)
        self._params = {
            key: kwargs.get(key, None)
                for key in self.__class__.__annotations__
        }
        # Перегрузка методов для экземпляра класса
        self.using = self.instance_using  # type: ignore

    def __getattr__(self, attr_name: str):
        return object.__getattribute__(self, attr_name)

    @classmethod
    def _set_global_instance(cls: Type[T], db_instance: redis.Redis) -> None:
        """ Установка глобальной ссылки на БД во время первого подключения """
        cls._db_instance = db_instance

    @classmethod
    def get(cls: Type[T], _items: list[T] = None, **kwargs) -> T:
        """
            Получение одного объекта по выбранному фильтру

                StorageItem.get(subsystem_id=10, tag_id=55)
        """
        result_list: list[T] = cls.filter(_items=_items, kwargs=kwargs)
        if not result_list:
            raise NotFoundException(f"{T} item not found...")
        if len(result_list) > 1:
            raise MoreThanOneFoundException(f"{T} multiple items found...")

        return result_list[0]

    @classmethod
    def filter(cls: Type[T], _items: list[T] = None, **kwargs) -> list[T]:
        """
            Получение объектов по фильтру переданных аргументов, например:

                StorageItem.get(subsystem_id=10, tag_id=55)
                StorageItem.get(subsystem_id__in=[10, 47], tag_id=55)
        """
        if not cls._db_instance:
            raise Exception("Redis database not connected...")
        if not len(kwargs) and not _items:
            raise Exception(f"{cls.__name__}.get() has empty filter. OOM possible.")
        # Формирование списка фильтров для возможности поиска входящих в список
        filters_list: list[str] = cls._get_filters_by_kwargs(kwargs=kwargs)
        result: list[T] = []
        for filter in filters_list:
            keys: list[bytes] = cls._db_instance.keys(pattern=filter)
            values: list[bytes] = cast(list[bytes], cls._db_instance.mget(keys))
            result += cls._objects_from_db_items(items=dict(zip(keys, values)))

        return result

    @classmethod
    def _objects_from_db_items(cls: Type[T], items: dict[bytes, bytes]) -> list[T]:
        """ Формирование cls(RedisItem)-объектов из данных базы """
        # Подготовка базовых данных для формирования объектов из ключей
        #   (уникальные ключи, без имён полей)
        tables: set[str] = {
            str(key).rsplit(KEYS_DELIMITER, 1)[0]
                for key in items.keys()
        }
        result_items: list[T] = []
        for table in tables:
            # Отбор полей с префиксом текущей table
            fields_src: list[bytes] = list(
                filter(lambda item: str(item).startswith(table), items)
            )
            fields: dict[str, Any] = {}
            for field in fields_src:
                # Формирование атрибутов объекта из присутствующих полей
                key: str = field.decode().rsplit(KEYS_DELIMITER, 1)[1]
                # Приведение типа к соответствующему полю cls
                if cls.__annotations__[key] is str:
                    fields[key] = items[field].decode()
                else:
                    fields[key] = cls.__annotations__[key](items[field])

            # Формирование Meta из table класса и префикса полученных данных
            table_args: dict = {}
            src_values: list[str] = table.split('.')
            for key, position in cls._table_keys.items():
                table_args[key] = src_values[position]

            result_items.append(cls(**(fields | table_args)))

        return result_items

    @staticmethod
    def _get_list_of_prepared_kwargs(kwargs: dict) -> list[dict]:
        """
            Подготовка списка фильтров из словарей:
                - исходный словарь разделить:
                    - базовый (без списков в значениях)
                    - расширенный (со списками в значениях)
                - получить множество комбинаций расширенного словаря
                - скомбинировать
        """
        basic_kwargs: dict = {}
        extend_kwargs: dict = {}
        # Разделение на словари "с" и "без" списков в значениях
        for key, value in kwargs.items():
            if not key.endswith(IN_PREFIX):
                basic_kwargs[key] = value
            else:
                extend_kwargs[key.strip(IN_PREFIX)] = value
        # Формирование итоговых словарей
        result_kwargs: list[dict] = []
        if extend_kwargs:
            # Получить множество комбинаций расширенного словаря
            mixed_kwargs: list[dict] = list(
                dict(zip(extend_kwargs.keys(), values))
                    for values in itertools.product(*extend_kwargs.values())
            )
            # Обогатить расширенные словари базовым
            result_kwargs = [mixed_item | basic_kwargs for mixed_item in mixed_kwargs]
        else:
            result_kwargs = [basic_kwargs]
        return result_kwargs

    @classmethod
    def _get_filters_by_kwargs(cls: Type[T], kwargs: dict) -> list[str]:
        """ Подготовка списка паттернов поиска """
        table: str = cls.Meta.table
        # Шаблон для поиска аргументов, которе не были переданы
        patterns: list[str] = re.findall(r'\{[^\}]*\}', table)
        str_filters: list[str] = []
        # Получение сырого списка фильтров
        prepared_kwargs_list: list[dict] = cls._get_list_of_prepared_kwargs(kwargs=kwargs)
        # Замена аргументов, которые не переданы, на звездочку
        for prepared_kwargs in prepared_kwargs_list:
            for pattern in patterns:
                clean_key: str = pattern.strip("{").strip("}")
                if not clean_key in prepared_kwargs:
                    table = table.replace(pattern, "*")
            # Заполнение паттерна поиска
            str_filters.append(table.format(**prepared_kwargs) + ".*")

        return str_filters

    @property
    def mapping(self) -> Mapping[_Key, _Value]:
        """ Формирование ключей и значений для БД """
        return {
            KEYS_DELIMITER.join([self._table, str(key)]): value
                for key, value in self._params.items()
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self._table=}, "
            f"{self._table_keys=}, {self._params=})"
        )

    def __eq__(self, other: Type[T]) -> bool:
        if isinstance(other, self.__class__):
            return self._params == other._params and self._table == other._table

        return False

    def instance_using(self: T, db_instance: redis.Redis = None) -> T:
        """
            Выполнение операций с БД путём direct-указания используемого
            подключения, например:

                another_client: redis.Redis = redis.Redis(host="8.8.8.8", db=12)
                storage_item_instance.using(db_instance=another_client).save()

            Создаётся копия объекта для работы через "неглобальное" подключение к Redis
        """
        copied_instance: T = copy.copy(self)
        copied_instance._db_instance = db_instance
        return copied_instance

    @classmethod
    def using(cls: Type[T], db_instance: redis.Redis = None) -> T:
        """
            Выполнение операций с БД путём direct-указания используемого
            подключения, например:

                another_client: redis.Redis = redis.Redis(host="8.8.8.8", db=12)
                StorageItem.using(db_instance=another_client).get(subsystem_id=10)

            Создаётся копия класса для работы через "неглобальное" подключение к Redis
        """
        class CopiedClass(cls):  # type: ignore
            _db_instance = db_instance
        CopiedClass.__annotations__.update(cls.__annotations__)
        return cast(T, CopiedClass)

    def save(self) -> OperationResult:
        """ Одиночная вставка """
        if not self._db_instance:
            raise Exception("Redis database not connected...")
        try:
            self._db_instance.mset(mapping=self.mapping)
            return OperationResult(status=OperationStatus.success)
        except Exception as exception:
            self._on_error_actions(exception=exception)
            return OperationResult(
                status=OperationStatus.failed,
                message=str(exception),
            )
