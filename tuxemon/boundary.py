# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


class BoundaryChecker:
    """
    A utility class for checking if a position is within a given boundary.
    Now supports setting a camera range and resetting to default.

    Attributes:
        default_x: The default invalid x-coordinate range.
        default_y: The default invalid y-coordinate range.
        invalid_x: The invalid x-coordinate range.
        invalid_y: The invalid y-coordinate range.
    """

    def __init__(self) -> None:
        self.default_x = (-1, 0)
        self.default_y = (-1, 0)
        self.invalid_x = self.default_x
        self.invalid_y = self.default_y

    def update_boundaries(self, map_size: tuple[int, int]) -> None:
        """
        Updates the invalid boundaries based on the given map size.

        Parameters:
            map_size: The size of the map (width, height).
        """
        self.invalid_x = (0, map_size[0])  # Exclusive upper bound
        self.invalid_y = (0, map_size[1])  # Exclusive upper bound

    def set_area(
        self,
        area_position: tuple[int, int],
        area_size: tuple[int, int],
        map_size: tuple[int, int],
    ) -> None:
        """
        Sets a new area with the specified position and size.

        Parameters:
            area_position: The position of the top-left corner of the
                new area (x, y).
            area_size: The size of the new area (width, height).
            map_size: The size of the larger map (width, height).

        Raises:
            ValueError: If the new area is outside the bounds of the map or
                if area_size contains non-positive values.
        """
        if any(x <= 0 for x in area_size):
            raise ValueError("Area size must have positive width and height.")

        start_x = max(0, area_position[0])
        end_x = min(map_size[0], area_position[0] + area_size[0])
        start_y = max(0, area_position[1])
        end_y = min(map_size[1], area_position[1] + area_size[1])

        if start_x >= end_x or start_y >= end_y:
            raise ValueError(
                "Invalid area: New area is outside the map bounds."
            )

        self.invalid_x = (start_x, end_x)
        self.invalid_y = (start_y, end_y)

    def set_area_from_center(
        self,
        center_position: tuple[int, int],
        radius: int,
        map_size: tuple[int, int],
    ) -> None:
        """
        Sets a new area with the specified center position and radius.

        Parameters:
            center_position: The center position of the new area (x, y).
            radius: The radius of the new area.
            map_size: The size of the larger map (width, height).

        Raises:
            ValueError: If the new area is outside the bounds of the map or
                if the radius is negative.
        """
        if radius < 0:
            raise ValueError("Radius must be non-negative.")

        start_x = max(0, center_position[0] - radius)
        end_x = min(map_size[0], center_position[0] + radius)  # No +1 here
        start_y = max(0, center_position[1] - radius)
        end_y = min(map_size[1], center_position[1] + radius)  # No +1 here

        if start_x >= end_x or start_y >= end_y:
            raise ValueError(
                "Invalid area: New area is outside the map bounds."
            )

        self.invalid_x = (start_x, end_x)
        self.invalid_y = (start_y, end_y)

    def reset_to_default(self) -> None:
        """
        Resets the boundaries to their default values (initially -1, 0).
        """
        self.invalid_x = self.default_x
        self.invalid_y = self.default_y

    def is_within_boundaries(self, position: tuple[float, float]) -> bool:
        """
        Checks if a given position is within the valid boundaries.

        Parameters:
            position: The position to check (x, y).

        Returns:
            bool: True if the position is within the boundaries, False otherwise.
        """
        return (
            self.invalid_x[0] <= position[0] < self.invalid_x[1]
            and self.invalid_y[0] <= position[1] < self.invalid_y[1]
        )

    def get_boundary_validity(
        self, position: tuple[float, float]
    ) -> tuple[bool, bool]:
        """
        Checks if a given position is within the valid boundaries.

        Parameters:
            position: The position to check (x, y).

        Returns:
            tuple[bool, bool]: A tuple of booleans indicating whether the position
            is within the x and y boundaries.
        """
        return (
            self.invalid_x[0] <= position[0] < self.invalid_x[1],
            self.invalid_y[0] <= position[1] < self.invalid_y[1],
        )

    def __repr__(self) -> str:
        return f"BoundaryChecker(invalid_x={self.invalid_x}, invalid_y={self.invalid_y})"
