import redis
from storage_orm import RedisItem
from storage_orm import OperationResult
from storage_orm import NotFoundException
from storage_orm import MoreThanOneFoundException

class ExampleItem(RedisItem):
    # Атрибуты объекта с указанием типа данных (в процессе сбора данных из БД приводится тип)
    date_time: int
    any_value: float

    class Meta:
        # Системный префикс записи в Redis
        # Ключи указанные в префиксе обязательны для передачи в момент создания экземпляра
        table = "subsystem.{subsystem_id}.tag.{tag_id}"

# Во время первого подключения устанавливается глобальное подключение к Redis
redis_1: redis.Redis = redis.Redis(host="localhost", port=8379, db=1)
redis_2: redis.Redis = redis.Redis(host="localhost", port=8379, db=2)
"""
    Во время создания orm_1 было назначено подключение для ExampleItem класса
    При использовании у экземпляра ExampleItem методов save/get будет использовано оно
"""

""" Запись в БД используя вызов save у экземпляра модели """
## Redis #1
example_item: ExampleItem = ExampleItem(subsystem_id=3, tag_id=15, date_time=1, any_value=11.)
result_of_operation: OperationResult = example_item.using(db_instance=redis_1).save()
## Redis #2
example_item: ExampleItem = ExampleItem(subsystem_id=3, tag_id=15, date_time=2, any_value=22.)
result_of_operation: OperationResult = example_item.using(db_instance=redis_2).save()

""" Получение записей """
try:
    item_from_redis_1: ExampleItem = ExampleItem.using(db_instance=redis_1).get(subsystem_id=3, tag_id=15)
    print(f"{item_from_redis_1=}")
except MoreThanOneFoundException:
    print("Найдено больше одной записи")
except NotFoundException:
    print("Не найдено ни одной записи с переданными параметрами")

item_from_redis_2: list[ExampleItem] = ExampleItem.using(db_instance=redis_2).filter(subsystem_id=3, tag_id=15)
print(f"{item_from_redis_2=}")
