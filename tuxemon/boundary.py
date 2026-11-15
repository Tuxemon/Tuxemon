# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from tuxemon.db import BoundingBox


class Dimensions(NamedTuple):
    width: float = 0.0
    height: float = 0.0
    radius: float = 0.0


class Boundary(ABC):
    """Interface for boundary types that support position checks."""

    @abstractmethod
    def is_within(self, position: tuple[float, float]) -> bool:
        pass

    @abstractmethod
    def get_dimensions(self) -> Dimensions:
        """Returns dimensions like width/height or radius."""

    @abstractmethod
    def get_center(self) -> tuple[float, float]:
        """Returns the center point of the boundary."""

    @abstractmethod
    def move(self, dx: float, dy: float) -> None:
        """Moves the boundary by the given deltas."""


class NullBoundary(Boundary):
    """A boundary that always returns False for any position."""

    def is_within(self, position: tuple[float, float]) -> bool:
        return False

    def get_dimensions(self) -> Dimensions:
        return Dimensions()

    def get_center(self) -> tuple[float, float]:
        return (0.0, 0.0)

    def move(self, dx: float, dy: float) -> None:
        pass  # No-op, since NullBoundary doesn't represent a real shape

    def __repr__(self) -> str:
        return "NullBoundary()"


class InvertedBoundary(Boundary):
    def __init__(self, base: Boundary):
        self.base = base

    def is_within(self, position: tuple[float, float]) -> bool:
        return not self.base.is_within(position)

    def get_dimensions(self) -> Dimensions:
        return self.base.get_dimensions()

    def get_center(self) -> tuple[float, float]:
        return self.base.get_center()

    def move(self, dx: float, dy: float) -> None:
        self.base.move(dx, dy)

    def __repr__(self) -> str:
        return f"InvertedBoundary(base={self.base})"


class TaggedBoundary(Boundary):
    def __init__(self, boundary: Boundary, tag: str):
        self.boundary = boundary
        self.tag = tag

    def is_within(self, position: tuple[float, float]) -> bool:
        return self.boundary.is_within(position)

    def get_dimensions(self) -> Dimensions:
        return self.boundary.get_dimensions()

    def get_center(self) -> tuple[float, float]:
        return self.boundary.get_center()

    def move(self, dx: float, dy: float) -> None:
        self.boundary.move(dx, dy)

    def __repr__(self) -> str:
        return f"TaggedBoundary(tag='{self.tag}', boundary={self.boundary})"


class RectangularBoundary(Boundary):
    """Defines a rectangular area with exclusive end coordinates."""

    def __init__(self, x_range: tuple[int, int], y_range: tuple[int, int]):
        self.x_range = x_range
        self.y_range = y_range

    def is_within(self, position: tuple[float, float]) -> bool:
        return (
            self.x_range[0] <= position[0] < self.x_range[1]
            and self.y_range[0] <= position[1] < self.y_range[1]
        )

    def get_dimensions(self) -> Dimensions:
        width = self.x_range[1] - self.x_range[0]
        height = self.y_range[1] - self.y_range[0]
        return Dimensions(width=width, height=height)

    def get_center(self) -> tuple[float, float]:
        center_x = (self.x_range[0] + self.x_range[1]) / 2
        center_y = (self.y_range[0] + self.y_range[1]) / 2
        return (center_x, center_y)

    def resize(self, dx: int, dy: int) -> None:
        """Resizes the rectangular boundary by expanding its width and height by the given deltas."""
        self.x_range = (self.x_range[0], self.x_range[1] + dx)
        self.y_range = (self.y_range[0], self.y_range[1] + dy)

    def move(self, dx: float, dy: float) -> None:
        """Moves the rectangular boundary by dx and dy."""
        self.x_range = (int(self.x_range[0] + dx), int(self.x_range[1] + dx))
        self.y_range = (int(self.y_range[0] + dy), int(self.y_range[1] + dy))

    def __repr__(self) -> str:
        return f"RectangularBoundary(x={self.x_range}, y={self.y_range})"


class CircularBoundary(Boundary):
    """Defines a circular area using center and radius."""

    def __init__(self, center: tuple[int, int], radius: int):
        if radius < 0:
            raise ValueError("Radius must be non-negative.")
        self.center = center
        self.radius_squared = radius * radius

    def is_within(self, position: tuple[float, float]) -> bool:
        dx = position[0] - self.center[0]
        dy = position[1] - self.center[1]
        return (dx * dx + dy * dy) <= self.radius_squared

    def get_dimensions(self) -> Dimensions:
        radius = math.sqrt(self.radius_squared)
        return Dimensions(radius=radius)

    def get_center(self) -> tuple[float, float]:
        return self.center

    def resize(self, delta: int) -> None:
        """Adjusts the radius by delta (positive or negative)."""
        new_radius = math.sqrt(self.radius_squared) + delta
        if new_radius < 0:
            raise ValueError("Resized radius must be non-negative.")
        self.radius_squared = int(new_radius * new_radius)

    def move(self, dx: float, dy: float) -> None:
        """Moves the circular boundary by dx and dy."""
        new_x = int(self.center[0] + dx)
        new_y = int(self.center[1] + dy)
        self.center = (new_x, new_y)

    def __repr__(self) -> str:
        return f"CircularBoundary(center={self.center}, radius={math.sqrt(self.radius_squared)})"


class CompositeBoundary(Boundary):
    """Combines multiple boundaries using union or intersection logic."""

    def __init__(self, boundaries: list[Boundary], mode: str = "union"):
        if mode not in {"union", "intersection"}:
            raise ValueError("Mode must be 'union' or 'intersection'.")
        self.boundaries = boundaries
        self.mode = mode

    def is_within(self, position: tuple[float, float]) -> bool:
        if self.mode == "union":
            return any(b.is_within(position) for b in self.boundaries)
        else:  # intersection
            return all(b.is_within(position) for b in self.boundaries)

    def get_dimensions(self) -> Dimensions:
        raise NotImplementedError(
            "CompositeBoundary does not support unified dimensions."
        )

    def get_center(self) -> tuple[float, float]:
        if not self.boundaries:
            return (0.0, 0.0)

        sum_x = sum(b.get_center()[0] for b in self.boundaries)
        sum_y = sum(b.get_center()[1] for b in self.boundaries)
        count = len(self.boundaries)
        return (sum_x / count, sum_y / count)

    def move(self, dx: float, dy: float) -> None:
        for b in self.boundaries:
            b.move(dx, dy)

    def __repr__(self) -> str:
        return f"CompositeBoundary(mode={self.mode}, count={len(self.boundaries)})"


class MapConditionBoundary(Boundary):
    def __init__(self, box: BoundingBox):
        self.x = float(box.x)
        self.y = float(box.y)
        self.width = box.width
        self.height = box.height

    def is_within(self, position: tuple[float, float]) -> bool:
        return (
            self.x < position[0] + 1
            and self.y < position[1] + 1
            and self.x + self.width > position[0]
            and self.y + self.height > position[1]
        )

    def get_dimensions(self) -> Dimensions:
        return Dimensions(width=float(self.width), height=float(self.height))

    def get_center(self) -> tuple[float, float]:
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        return (center_x, center_y)

    def move(self, dx: float, dy: float) -> None:
        """Moves the boundary by dx and dy."""
        self.x += dx
        self.y += dy

    def resize(self, dx: int, dy: int) -> None:
        """Resizes the boundary by expanding width and height."""
        self.width = max(0, self.width + dx)
        self.height = max(0, self.height + dy)

    def __repr__(self) -> str:
        return (
            f"MapConditionBoundary(x={self.x}, y={self.y}, "
            f"width={self.width}, height={self.height})"
        )


class BoundaryChecker:
    """Manages a single active boundary and checks positions against it."""

    def __init__(self) -> None:
        self.boundaries: dict[str, Boundary] = {}
        self.active: str | None = None

    def set_rectangular_boundary(
        self, name: str, x0: int, x1: int, y0: int, y1: int
    ) -> None:
        """Sets a rectangular boundary using start and end coordinates."""
        self.boundaries[name] = RectangularBoundary((x0, x1), (y0, y1))
        self.set_active(name)

    def set_circular_boundary(
        self, name: str, center: tuple[int, int], radius: int
    ) -> None:
        """Sets a circular boundary using center and radius."""
        self.boundaries[name] = CircularBoundary(center, radius)
        self.set_active(name)

    def set_active(self, name: str) -> None:
        """Sets the active boundary by name."""
        if name not in self.boundaries:
            raise ValueError(f"Boundary '{name}' not found.")
        self.active = name

    def get_active_boundary(self) -> Boundary:
        """Returns the currently active boundary or a fallback if none is set."""
        if self.active is None:
            return NullBoundary()
        return self.boundaries[self.active]

    def reset_to_default(self) -> None:
        """Resets the boundary to reject all positions."""
        self.boundaries["default"] = NullBoundary()
        self.set_active("default")

    def is_within_boundaries(self, position: tuple[float, float]) -> bool:
        """Checks if a position is within the current boundary."""
        return self.get_active_boundary().is_within(position)

    def get_boundary_validity(
        self, position: tuple[float, float]
    ) -> tuple[bool, bool]:
        """Returns (x_valid, y_valid) for rectangular boundaries only."""
        boundary = self.get_active_boundary()
        if isinstance(boundary, RectangularBoundary):
            x_valid = boundary.x_range[0] <= position[0] < boundary.x_range[1]
            y_valid = boundary.y_range[0] <= position[1] < boundary.y_range[1]
            return (x_valid, y_valid)
        raise TypeError(
            "Boundary validity only supported for RectangularBoundary."
        )

    def __repr__(self) -> str:
        return f"BoundaryChecker(boundary={self.get_active_boundary()})"
