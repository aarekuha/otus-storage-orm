#### StorageORM (OTUS проектная работа)
##### Зависимости
- [redis-py](https://github.com/redis/redis-py)
##### Базовый пример использования ([все примеры](examples/), [базовый пример](examples/redis_1_single.py))
1. Импорт классов
    ```python
        from storage_orm import StorageORM
        from storage_orm import RedisORM
        from storage_orm import RedisItem
        from storage_orm import OperationResult
    ```
1. Определить модель
    ```python
        class ExampleItem(RedisItem):
            """
                Атрибуты объекта с указанием типа данных
                  (в процессе сбора данных из БД приводится тип)
            """
            date_time: int
            any_value: float

            class Meta:
                """
                    Системный префикс записи в Redis
                    Ключи указанные в префиксе обязательны для
                      передачи в момент создания экземпляра
                """
                table = "subsystem.{subsystem_id}.tag.{tag_id}"
    ```
1. Установить подключение ORM можно двумя способами
    1. Передать данные для подключения непосредственно в ORM
        ```python
            orm: StorageORM = RedisORM(host="localhost", port=8379, db=1)
        ```
    1. Создать подключение redis.Redis и передать его в конструктор
        ```python
            redis: redis.Redis = redis.Redis(host="localhost", port=8379, db=1)
            orm: StorageORM = RedisORM(db=redis)
        ```
1. Добавление/редактирование записи (ключами записи являются параметры, указанные в Meta.table модели)
    1. Создать объект на основе модели
        ```python
            example_item: ExampleItem = ExampleItem(
                subsystem_id=3,
                tag_id=15,
                date_time=100,
                any_value=17.
            )
        ```
    1. Выполнить вставку можно несколькими способами
        1. Использовать метод save() созданного экземпляра
            ```python
                operation_result: OperationResult = example_item.save()
            ```
        1. Использовать метод save() StorageOrm
            ```python
                operation_result: OperationResult = orm.save(item=example_item)
            ```
        1. Использовать **групповую** вставку записей ([пример групповой вставки](examples/redis_2_bulk_multiple.py))
            ```python
                operation_result: OperationResult = orm.bulk_create(
                    items=[example_item1, example_item2]
                )
            ```
1. Выборка данных из БД
    - для выборки необходимо передать аргументы для параметров, которые используются в Meta.table
        ```python
            table = "subsystem.{subsystem_id}.tag.{tag_id}"
                                     ^               ^
        ```
        , например
        ```python
            example_items: list[exampleitem] = exampleitem.get(subsystem_id=3, tag_id=15)
        ```
1. Использование нескольких подключений ([пример](examples/redis_3_using_multiple_connections.py))
    - для использования нескольких подключений необходимо в метод StorageItem.using(db_instance=...) передать
      подготовленное соединение с БД Redis, например
        ```python
            redis_another: redis.Redis = redis.Redis(host="localhost", port=8379, db=17)
            ...
            result_of_operation: OperationResult = example_item.using(db_instance=redis_another).save()
        ```


##### Запуск примеров
```bash
    python -m venv venv
    source ./venv/bin/activate
    pip install redis

    # Базовый простой пример
    PYTHONPATH="${PYTHONPATH}:." python examples/redis_1_single.py

    # Пример групповой вставки (bulk)
    PYTHONPATH="${PYTHONPATH}:." python examples/redis_2_bulk_multiple.py

    # Пример использования нескольких подключений
    PYTHONPATH="${PYTHONPATH}:." python examples/redis_3_using_multiple_connections.py
```
