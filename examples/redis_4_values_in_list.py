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

# Создание трёх записей с последовательным subsystem_id
items: list[ExampleItem] = []
for i in range(3):
    items.append(ExampleItem(subsystem_id=21+i, tag_id=15, date_time=100+i, any_value=17.+i))
result_of_operation: OperationResult = orm.bulk_create(items=items)
print(result_of_operation)

# Получение всех записей по фильтру
getted_items: list[ExampleItem] = ExampleItem.filter(subsystem_id__in=[21, 23], tag_id=15)
for item in getted_items:
    print(f"{item=}")

