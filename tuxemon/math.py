# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Math utilities that can be used without Pygame.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator, Sequence
from typing import TypeVar, Union, overload

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sequence) or len(self) != len(other):
            return NotImplemented

        return tuple(self) == tuple(other)

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
        key: Union[int, slice],
    ) -> Union[float, Sequence[float]]:
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
        x: Union[float, Sequence[float]] = 0,
        y: float = 0,
        z: float = 0,
    ) -> None:
        if isinstance(x, (int, float)):
            self.x = x
            self.y = y
            self.z = z
        else:
            self.x, self.y, self.z = x

    def __iter__(self) -> Generator[float, None, None]:
        yield self.x
        yield self.y
        yield self.z


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
        x: Union[float, Sequence[float]] = 0,
        y: float = 0,
    ) -> None:
        if isinstance(x, (int, float)):
            self.x = x
            self.y = y
        else:
            self.x, self.y = x

    def __iter__(self) -> Generator[float, None, None]:
        yield self.x
        yield self.y


Point3 = Vector3
Point2 = Vector2
