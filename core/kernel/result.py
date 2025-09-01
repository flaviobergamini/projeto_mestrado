from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):
    value: Optional[T] = None
    error: Optional[E] = None
    bad_request_error: Optional[E] = None
    not_found_error: Optional[E] = None
    unauthorized_error: Optional[E] = None

    @property
    def is_ok(self) -> bool:
        return self.error is None and self.bad_request_error is None and self.not_found_error is None and self.unauthorized_error is None

    @property
    def is_err(self) -> bool:
        return self.error is not None or self.bad_request_error is not None or self.not_found_error is not None and self.unauthorized_error is not None
    
    @property
    def is_bad_request(self) -> bool:
        return self.bad_request_error is not None
    
    @property
    def is_not_found(self) -> bool:
        return self.not_found_error is not None
    
    @property
    def is_unauthorized(self) -> bool:
        return self.unauthorized_error is not None

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        return Result(value=value)

    @staticmethod
    def err(error: E) -> "Result[T, E]":
        return Result(error=error)
    
    @staticmethod
    def bad_request(error: E) -> "Result[T, E]":
        return Result(bad_request_error=error)
    
    @staticmethod
    def not_found(error: E) -> "Result[T, E]":
        return Result(not_found_error=error)
    
    @staticmethod
    def unauthorized(error: E) -> "Result[T, E]":
        return Result(unauthorized_error=error)