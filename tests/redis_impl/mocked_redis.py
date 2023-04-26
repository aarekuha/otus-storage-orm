from __future__ import annotations
import redis


class MockedRedis(redis.Redis):
    calls_count: int
    execute_calls_count: int
    _pipe: MockedRedis

    def __init__(self, is_pipe: bool = False) -> None:
        self.calls_count = 0
        self.execute_calls_count = 0
        if not is_pipe:
            self._pipe = self.__class__(is_pipe=True)

    def mset(self, **_) -> None:
        self.calls_count += 1

    def execute(self, **_) -> None:
        self.execute_calls_count += 1

    def pipeline(self, **_) -> MockedRedis:
        return self._pipe
