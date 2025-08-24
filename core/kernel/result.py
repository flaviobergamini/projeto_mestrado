from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):
    value: Optional[T] = None
    error: Optional[E] = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @property
    def is_err(self) -> bool:
        return self.error is not None

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        return Result(value=value)

    @staticmethod
    def err(error: E) -> "Result[T, E]":
        return Result(error=error)
