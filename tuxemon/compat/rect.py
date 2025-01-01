# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol, TypeVar, Union, cast, runtime_checkable

SelfRectType = TypeVar("SelfRectType", bound="ReadOnlyRect")
RectType = TypeVar("RectType", bound="ReadOnlyRect", covariant=True)


@runtime_checkable
class HasRectAttribute(Protocol[RectType]):
    @property
    def rect(self) -> RectType:
        pass


RectLike = Union[
    SelfRectType,
    tuple[int, int, int, int],
    tuple[tuple[int, int], tuple[int, int]],
]


class ReadOnlyRect(Protocol):
    """Interface of a PyGame compatible rect."""

    def __init__(
        self: SelfRectType,
        __arg: Union[HasRectAttribute[SelfRectType], RectLike[SelfRectType]],
    ) -> None:
        pass

    def copy(self: SelfRectType) -> SelfRectType:
        return type(self)((self.x, self.y, self.w, self.h))

    def move(self: SelfRectType, x: int, y: int) -> SelfRectType:
        return type(self)((self.x + x, self.y + y, self.w, self.h))

    def inflate(self: SelfRectType, x: int, y: int) -> SelfRectType:
        return type(self)(
            (
                self.x - type(self.x)(x / 2),
                self.y - type(self.y)(y / 2),
                self.w + x,
                self.h + y,
            )
        )

    def union(
        self: SelfRectType,
        __other: RectLike[SelfRectType],
    ) -> SelfRectType:
        return self.unionall((__other,))

    def unionall(
        self: SelfRectType,
        __rects: Sequence[RectLike[SelfRectType]],
    ) -> SelfRectType:
        rects_list = [type(self)(r) for r in __rects] + [self]
        left = min(r.left for r in rects_list)
        top = min(r.top for r in rects_list)
        right = max(r.right for r in rects_list)
        bottom = max(r.bottom for r in rects_list)
        return type(self)((left, top, right - left, bottom - top))

    def contains(
        self: SelfRectType,
        __other: RectLike[SelfRectType],
    ) -> bool:
        other = type(self)(__other)
        return (
            (self.left <= other.left)
            and (self.top <= other.top)
            and (self.right >= other.right)
            and (self.bottom >= other.bottom)
            and (self.right > other.left)
            and (self.bottom > other.top)
        )

    def collidepoint(
        self,
        __point: tuple[int, int],
    ) -> bool:
        x, y = __point
        return self.left <= x < self.right and self.top <= y < self.bottom

    def colliderect(
        self: SelfRectType,
        __other: RectLike[SelfRectType],
    ) -> bool:
        return intersect(self, type(self)(__other))

    def collidelist(
        self: SelfRectType,
        __rects: Sequence[RectLike[SelfRectType]],
    ) -> int:
        for i, rect in enumerate(__rects):
            if intersect(self, type(self)(rect)):
                return i
        return -1

    def collidelistall(
        self: SelfRectType,
        __l: Sequence[RectLike[SelfRectType]],
    ) -> Sequence[int]:
        return [
            i
            for i, rect in enumerate(__l)
            if intersect(self, type(self)(rect))
        ]

    @property
    def top(self) -> int:
        return self.y

    @property
    def left(self) -> int:
        return self.x

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def topleft(self) -> tuple[int, int]:
        return self.x, self.y

    @property
    def bottomleft(self) -> tuple[int, int]:
        return self.x, self.y + self.h

    @property
    def topright(self) -> tuple[int, int]:
        return self.x + self.w, self.y

    @property
    def bottomright(self) -> tuple[int, int]:
        return self.x + self.w, self.y + self.h

    @property
    def midtop(self) -> tuple[int, int]:
        return self.centerx, self.y

    @property
    def midleft(self) -> tuple[int, int]:
        return self.x, self.centery

    @property
    def midbottom(self) -> tuple[int, int]:
        return self.centerx, self.y + self.h

    @property
    def midright(self) -> tuple[int, int]:
        return self.x + self.w, self.centery

    @property
    def center(self) -> tuple[int, int]:
        return self.centerx, self.centery

    @property
    def centerx(self) -> int:
        return self.x + self.w // 2

    @property
    def centery(self) -> int:
        return self.y + self.h // 2

    @property
    def size(self) -> tuple[int, int]:
        return self.w, self.h

    @property
    def width(self) -> int:
        return self.w

    @property
    def height(self) -> int:
        return self.h

    @property
    @abstractmethod
    def w(self) -> int:
        pass

    @property
    @abstractmethod
    def h(self) -> int:
        pass

    @property
    @abstractmethod
    def x(self) -> int:
        pass

    @property
    @abstractmethod
    def y(self) -> int:
        pass


def intersect(r1: ReadOnlyRect, r2: ReadOnlyRect) -> bool:
    return (
        (r2.left <= r1.left < r2.right) or (r1.left <= r2.left < r1.right)
    ) and ((r2.top <= r1.top < r2.bottom) or (r1.top <= r2.top < r1.bottom))


class Rect(ReadOnlyRect):
    """
    Pure Python Rect class that follows the PyGame API

    GIANT WARNING: This is completely in python and will be much slower than
                   PyGame's built in Rect class.  This rect should be used only
                   if needed!

    These rects support floating point and are hashable.
    """

    __slots__ = ["_x", "_y", "_w", "_h"]

    def __init__(
        self,
        arg: Union[HasRectAttribute[Rect], RectLike[Rect]],
    ) -> None:
        """
        should accept rect like object or tuple of two tuples or one tuple
        of four numbers, store :x,y,h,w
        """
        if isinstance(arg, HasRectAttribute):
            arg = arg.rect

        if isinstance(arg, Rect):
            self._x = arg.x
            self._y = arg.y
            self._w = arg.w
            self._h = arg.h
        elif isinstance(arg, (list, tuple)):
            if len(arg) == 2:
                arg = cast(tuple[tuple[int, int], tuple[int, int]], arg)
                self._x, self._y = arg[0]
                self._w, self._h = arg[1]
            elif len(arg) == 4:
                arg = cast(tuple[int, int, int, int], arg)
                self._x, self._y, self._w, self._h = arg
        else:
            self._x, self._y, self._w, self._h = arg

    @property
    def w(self) -> int:
        return self._w

    @property
    def h(self) -> int:
        return self._h

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y
