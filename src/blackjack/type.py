from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)


@dataclass
class Ok(Generic[T]):
    val: T


@dataclass
class Err(Generic[E]):
    val: E


Result = Ok[T] | Err[E]
