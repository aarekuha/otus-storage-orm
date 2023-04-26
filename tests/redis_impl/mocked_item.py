from storage_orm import RedisItem


class MockedItem(RedisItem):
    calls_count: int

    def __init__(self) -> None:
        self.calls_count = 0

    def save(self) -> None:
        self.calls_count += 1

    def mapping(self) -> None:
        return None
