from time import monotonic

from storage_orm import RedisORM
from storage_orm import RedisItem
from storage_orm import StorageORM

COUNT: int = 100_000


class TestItem(RedisItem):
    attr1: int
    attr2: str

    class Meta:
        table = "param1.{param1}.param2.{param2}"


# Write test
start_time: float = monotonic()
redis_orm: StorageORM = RedisORM(host="localhost", port=8379, db=1)
redis_orm.bulk_create([TestItem(attr1=i, attr2=str(i), param1=i%5, param2=i%3) for i in range(COUNT)])
total_time: float = monotonic() - start_time
print(f"StorageORM (write) -> Objects count: {COUNT}, total time: {total_time}")
# Load test (direct)
start_time: float = monotonic()
items: list[TestItem] = TestItem.filter(param1=1, param2=1)
total_time: float = monotonic() - start_time
print(f"StorageORM (load, direct) -> Objects count: {COUNT}, total time: {total_time}")
# Load test (use parameter __in)
start_time: float = monotonic()
items: list[TestItem] = TestItem.filter(param1__in=[1,2,3,4,5,6,7], param2=1)
total_time: float = monotonic() - start_time
print(f"StorageORM (load, use __in = [1-7]) -> Objects count: {COUNT}, total time: {total_time}")
