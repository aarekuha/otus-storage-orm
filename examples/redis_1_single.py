from storage_orm import StorageORM
from storage_orm import RedisORM
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
orm: StorageORM = RedisORM(host="localhost", port=8379)

# Создание единичной записи
example_item: ExampleItem = ExampleItem(subsystem_id=3, tag_id=15, date_time=100, any_value=17.)
result_of_operation: OperationResult = example_item.save()
print(result_of_operation)

# Получение одной записи
try:
    getted_item: ExampleItem = ExampleItem.get(subsystem_id__in=3, tag_id=15)
    print(f"{getted_item=}")
except MoreThanOneFoundException:
    print("Найдено больше одной записи")
except NotFoundException:
    print("Не найдено ни одной записи с переданными параметрами")


# Получение всех записей по фильтру
getted_items: list[ExampleItem] = ExampleItem.filter(subsystem_id=3, tag_id=15)
print(f"{getted_items=}")

