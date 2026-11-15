# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypeVar, overload

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig

TVarSequence = TypeVar("TVarSequence", bound=tuple[int, ...])


def make_default_scaling(
    config: TuxemonConfig, native_resolution: tuple[int, int]
) -> DefaultScaling:
    if config.large_gui:
        scale = 2
    elif config.scaling:
        scale = int(config.resolution[0] / native_resolution[0])
    else:
        scale = 1

    return DefaultScaling(scale)


class ScalingStrategy(Protocol):
    """
    Strategy interface for scaling coordinate tuples.
    """

    def scale_tuple(self, coords: TVarSequence) -> TVarSequence: ...
    def scale_int(self, value: int) -> int: ...
    def scale_float(self, value: float) -> float: ...
    def scale_sequence(self, seq: Sequence[float]) -> list[float]: ...
    def scale_point(self, point: tuple[int, int]) -> tuple[int, int]: ...


class DefaultScaling:
    def __init__(self, scale: int):
        self._scale = scale

    def scale_tuple(self, coords: TVarSequence) -> TVarSequence:
        return type(coords)(i * self._scale for i in coords)

    def scale_int(self, value: int) -> int:
        return value * self._scale

    def scale_float(self, value: float) -> float:
        return value * self._scale

    def scale_sequence(self, seq: Sequence[float]) -> list[float]:
        return [self.scale_float(x) for x in seq]

    def scale_point(self, point: tuple[int, int]) -> tuple[int, int]:
        x, y = point
        return (x * self._scale, y * self._scale)


class ResolutionScaling:
    def __init__(
        self,
        base_resolution: tuple[int, int],
        current_resolution: tuple[int, int],
    ):
        self.base_w, self.base_h = base_resolution
        self.curr_w, self.curr_h = current_resolution

    def scale_int(self, value: int) -> int:
        # scale uniformly using width ratio
        return int(value * (self.curr_w / self.base_w))

    def scale_float(self, value: float) -> float:
        return value * (self.curr_w / self.base_w)

    def scale_sequence(self, seq: Sequence[float]) -> list[float]:
        return [self.scale_float(x) for x in seq]

    @overload
    def scale_tuple(self, coords: tuple[int, int]) -> tuple[int, int]: ...
    @overload
    def scale_tuple(
        self, coords: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]: ...

    def scale_tuple(
        self, coords: tuple[int, int] | tuple[int, int, int, int]
    ) -> tuple[int, int] | tuple[int, int, int, int]:
        sx = self.curr_w / self.base_w
        sy = self.curr_h / self.base_h

        if len(coords) == 2:
            w, h = coords
            return (int(w * sx), int(h * sy))

        if len(coords) == 4:
            x, y, w, h = coords
            return (int(x * sx), int(y * sy), int(w * sx), int(h * sy))

        raise ValueError("ResolutionScaling only supports 2- or 4-tuples")

    def scale_point(self, point: tuple[int, int]) -> tuple[int, int]:
        x, y = point
        sx = self.curr_w / self.base_w
        sy = self.curr_h / self.base_h
        return (int(x * sx), int(y * sy))
