from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar
import math

T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)


@dataclass
class Ok(Generic[T]):
    val: T


@dataclass
class Err(Generic[E]):
    val: E


Result = Ok[T] | Err[E]


def get_evenly_spaced_points(w: float, x: float, s: int) -> List[float]:
    """
    Where you want to evenly space s intervals of length x on an interval of length w
    Returns an n-length list [P(1), P(2), P(3), ... P(n)]
    of the leftmost values P(n) for each interval with respect to w, where 0<=P(n)<w

    Generalised using linear algebra:
    ```
    If there are s evenly spaced zones of width x on a line of length w, and the space between is m,
    Then there are s intervals and s+1 spaces on the interval of length w
    So,     (s+1)m + sx = w => m = (w-sx)/(s+1)
    The leftmost point P(1) = m
            P(2) = m + (x+m)  = (2w + x(1-s))/(s+1)
            P(3) = m + 2(x+m) = (3w + x(2-s))/(s+1)
    and so on,
    Thus,   P(n) = m + n(x+m) = (nw + x(n-1-s))/(s+1)
    ```
    """
    return [(n * w + x * (n - 1 - s)) / (s + 1) for n in range(1, s + 1)]


class Vec2:
    def __init__(self, x: float, y: float) -> None:
        """
        <0 0> is the top left corner
        x increases rightward
        y increases downward
        """
        self.x = x
        self.y = y

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def magn(self) -> float:
        """Returns the magnitude/length of the vector"""
        return math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))

    def unit(self) -> Vec2:
        """Returns the unit vector"""
        modulus = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        return Vec2(self.x / modulus, self.y / modulus)
