import pytest

from storage_orm import RedisORM
from storage_orm import RedisItem

from .mocked_item import MockedItem
from .mocked_redis import MockedRedis


@pytest.fixture
def mocked_redis() -> MockedRedis:
    return MockedRedis()


def test_empty_constructor() -> None:
    """ Отсутствие аргументов для подключения """
    with pytest.raises(Exception) as exception:
        RedisORM()

    assert "must contains" in str(exception.value)


def test_save_calls_item_method(mocked_redis: MockedRedis) -> None:
    """
        Вызов метода сохранение одного элемента должен
            вызывать метод у самого элемента
    """
    mocked_item: MockedItem = MockedItem()
    RedisORM(client=mocked_redis).save(item=mocked_item)
    assert mocked_item.calls_count == 1


def test_bulk_create_calls_methods(mocked_redis: MockedRedis) -> None:
    """
        Вызов метода группового сохранения должен вызывать у
            pipe методы mset для каждого объекта и закрывать
            транзакцию вызовом метода execute
    """
    items_count: int = 11
    items: list[MockedItem] = [MockedItem() for _ in range(items_count)]
    RedisORM(client=mocked_redis).bulk_create(items=items)
    assert mocked_redis._pipe.calls_count == items_count
    assert mocked_redis._pipe.execute_calls_count == 1


def test_init_global_db_connection(mocked_redis: MockedRedis) -> None:
    """
        При первом подключении должна устанавливаться глобальная
            ссылка на него
    """
    # Удалить установленное подключение
    RedisItem._db_instance = None
    # Создать новое и проверить, что именно оно проинициализировалось
    RedisORM(client=mocked_redis)
    assert id(MockedItem._db_instance) == id(mocked_redis)


def test_noreinit_global_db_connection(mocked_redis: MockedRedis) -> None:
    """
        При первом подключении должна устанавливаться глобальная
            ссылка на него
    """
    # Установить стороннее подключение в случае отсутствия
    if RedisItem._db_instance is None:
        RedisORM(client=MockedRedis())
    # Создать новое и проверить, что сохранилось первое подключение
    RedisORM(client=mocked_redis)
    assert id(MockedItem._db_instance) != id(mocked_redis)
