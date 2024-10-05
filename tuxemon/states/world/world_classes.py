# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


class BoundaryChecker:
    """
    A utility class for checking if a position is within a given boundary.

    Attributes:
        invalid_x: The invalid x-coordinate range.
        invalid_y: The invalid y-coordinate range.
    """

    def __init__(self) -> None:
        self.invalid_x = (-1, 0)
        self.invalid_y = (-1, 0)

    def update_boundaries(self, map_size: tuple[int, int]) -> None:
        """
        Updates the invalid boundaries based on the given map size.

        Parameters:
            map_size: The size of the map (width, height).
        """
        self.invalid_x = (-1, map_size[0])
        self.invalid_y = (-1, map_size[1])

    def is_within_boundaries(self, position: tuple[float, float]) -> bool:
        """
        Checks if a given position is within the valid boundaries.

        Parameters:
            position: The position to check (x, y).

        Returns:
            bool: True if the position is within the boundaries, False otherwise.
        """
        return (
            self.invalid_x[0] < position[0] < self.invalid_x[1]
            and self.invalid_y[0] < position[1] < self.invalid_y[1]
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
            self.invalid_x[0] < position[0] < self.invalid_x[1],
            self.invalid_y[0] < position[1] < self.invalid_y[1],
        )

    def __repr__(self) -> str:
        return f"BoundaryChecker(invalid_x={self.invalid_x}, invalid_y={self.invalid_y})"
