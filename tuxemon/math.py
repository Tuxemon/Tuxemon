# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Math utilities that can be used without Pygame.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator, Sequence
from math import sqrt
from typing import TypeVar, overload

SelfType = TypeVar("SelfType", bound="Vector")


class Vector(ABC, Sequence[float]):
    @abstractmethod
    def __init__(
        self,
        values: Sequence[float],
        /,
    ) -> None:
        pass

    def __str__(self) -> str:
        return f"{type(self)}{tuple(self)}"

    @property
    def magnitude(self) -> float:
        return sqrt(sum(component**2 for component in self))

    @property
    def normalized(self: SelfType) -> SelfType:
        """
        Returns the normalized vector (unit vector).
        """
        if self.magnitude == 0:
            return type(self)([0] * len(self))
        return self * (1 / self.magnitude)

    @property
    def as_tuple(self) -> tuple[float, ...]:
        return tuple(self)

    def __len__(self) -> int:
        return len(tuple(iter(self)))

    @overload
    def __getitem__(self, key: int) -> float:
        pass

    @overload
    def __getitem__(self, key: slice) -> Sequence[float]:
        pass

    def __getitem__(
        self,
        key: int | slice,
    ) -> float | Sequence[float]:
        return tuple(self)[key]

    def __add__(self: SelfType, other: Sequence[float]) -> SelfType:
        return type(self)([s + o for s, o in zip(self, other)])

    def __mul__(self: SelfType, scalar: float) -> SelfType:
        return type(self)([s * scalar for s in self])

    def __rmul__(self: SelfType, scalar: float) -> SelfType:
        return self * scalar


class Vector3(Vector):
    @overload
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        values: Sequence[float],
        /,
    ) -> None:
        pass

    def __init__(
        self,
        x: float | Sequence[float] = 0,
        y: float = 0,
        z: float = 0,
    ) -> None:
        if isinstance(x, (int, float)):
            self.x = x
            self.y = y
            self.z = z
        else:
            self.x, self.y, self.z = x

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector3):
            return (self.x, self.y, self.z) == (other.x, other.y, other.z)
        if isinstance(other, Sequence) and len(other) == 3:
            return (self.x, self.y, self.z) == tuple(other)
        return False

    def __iter__(self) -> Generator[float, None, None]:
        yield self.x
        yield self.y
        yield self.z

    def __mul__(self, scalar: float) -> Vector3:
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> Vector3:
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __sub__(self, other: Vector3 | Sequence[float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3(
                self.x - other.x, self.y - other.y, self.z - other.z
            )
        elif isinstance(other, (tuple, list)) and len(other) == 3:
            return Vector3(
                self.x - other[0], self.y - other[1], self.z - other[2]
            )
        raise TypeError(
            f"Unsupported operand type(s) for -: 'Vector3' and '{type(other).__name__}'"
        )

    def __rsub__(self, other: Vector3 | Sequence[float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3(
                other.x - self.x, other.y - self.y, other.z - self.z
            )
        elif isinstance(other, (tuple, list)) and len(other) == 3:
            return Vector3(
                other[0] - self.x, other[1] - self.y, other[2] - self.z
            )
        raise TypeError(
            f"Unsupported operand type(s) for -: '{type(other).__name__}' and 'Vector3'"
        )

    def copy(self) -> Vector3:
        return Vector3(self.x, self.y, self.z)

    def __repr__(self) -> str:
        return f"Vector3({self.x}, {self.y}, {self.z})"


class Vector2(Vector):
    @overload
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        values: Sequence[float],
        /,
    ) -> None:
        pass

    def __init__(
        self,
        x: float | Sequence[float] = 0,
        y: float = 0,
    ) -> None:
        if isinstance(x, (int, float)):
            self.x = x
            self.y = y
        else:
            self.x, self.y = x

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2):
            return (self.x, self.y) == (other.x, other.y)
        if isinstance(other, Sequence) and len(other) == 2:
            return (self.x, self.y) == tuple(other)
        return False

    def __iter__(self) -> Generator[float, None, None]:
        yield self.x
        yield self.y

    def __add__(self, other: Vector2 | Sequence[float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Vector2(self.x + other[0], self.y + other[1])
        raise TypeError(
            f"Unsupported operand type(s) for +: 'Vector2' and '{type(other).__name__}'"
        )

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> Vector2:
        return Vector2(self.x / scalar, self.y / scalar)

    def __sub__(self, other: Vector2 | Sequence[float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Vector2(self.x - other[0], self.y - other[1])
        raise TypeError(
            f"Unsupported operand type(s) for -: 'Vector2' and '{type(other).__name__}'"
        )

    def __rsub__(self, other: Vector2 | Sequence[float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2(other.x - self.x, other.y - self.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Vector2(other[0] - self.x, other[1] - self.y)
        raise TypeError(
            f"Unsupported operand type(s) for -: '{type(other).__name__}' and 'Vector2'"
        )

    def copy(self) -> Vector2:
        return Vector2(self.x, self.y)

    def __repr__(self) -> str:
        return f"Vector2({self.x}, {self.y})"
