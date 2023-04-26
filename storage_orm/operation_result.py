from enum import Enum
from typing import Union


class OperationStatus(Enum):
    """ Статус операции записи/чтения из БД """
    success = True
    failed = False


class OperationResult:
    """ Результат записи/чтения из БД """
    status: OperationStatus
    message: str

    def __init__(self, status: Union[OperationStatus, bool], message: str = "") -> None:
        self.status = OperationStatus(status)
        self.message = message

    @property
    def ok(self) -> bool:
        return self.status == OperationStatus.success

    def __str__(self) -> str:
        message: str = f", message={self.message}" if self.message else ""
        return f"{self.__class__.__name__}: status={self.status}{message}"
