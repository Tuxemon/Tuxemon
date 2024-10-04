# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import prepare
from tuxemon.math import Vector2
from tuxemon.platform.const import intentions

if TYPE_CHECKING:
    from tuxemon.entity import Entity
    from tuxemon.platform.events import PlayerInput
    from tuxemon.states.world.world_classes import BoundaryChecker

SPEED_UP: int = 7
SPEED_DOWN: int = 7
SPEED_LEFT: int = 7
SPEED_RIGHT: int = 7


def project(position: Sequence[float]) -> tuple[int, int]:
    return (
        int(position[0] * prepare.TILE_SIZE[0]),
        int(position[1] * prepare.TILE_SIZE[1]),
    )


def unproject(position: Sequence[float]) -> tuple[int, int]:
    return (
        int(position[0] / prepare.TILE_SIZE[0]),
        int(position[1] / prepare.TILE_SIZE[1]),
    )


class Camera:
    """
    A camera class that follows a entity object in a game or simulation.

    Attributes:
        entity: The entity object that the camera follows.
        tile_size: The size of the tiles in the game world.
        position: The current position of the camera.
        follows_entity: Whether the camera is currently following the entity.
        original_entity: The original entity object that the camera follows.
        boundary: A utility class for checking if a position is within a given
            boundary.
    """

    def __init__(self, entity: Entity[Any], boundary: BoundaryChecker):
        """
        Initializes the camera with a reference to a entity object.

        Parameters:
            entity: The entity object that the camera follows.
            boundary: A utility class for checking if a position is within a
                given boundary.
        """
        self.entity = entity
        self.original_entity = entity
        self.tile_size = prepare.TILE_SIZE
        self.position = self.get_entity_center()
        self.follows_entity = True
        self.free_roaming_enabled = False
        self.boundary = boundary

    def follow(self) -> None:
        """
        Start the camera following the current entity.
        """
        self.follows_entity = True

    def unfollow(self) -> None:
        """
        Stop the camera from following the current entity.
        """
        self.follows_entity = False

    def get_center(self, position: Vector2) -> Vector2:
        """
        Returns the center of a tile given its position.

        Parameters:
            position: The position of the tile.

        Returns:
            Vector2: The center of the tile.
        """
        cx, cy = project(position)
        return Vector2(
            cx + self.tile_size[0] // 2, cy + self.tile_size[1] // 2
        )

    def get_entity_center(self) -> Vector2:
        """
        Returns the center of the entity's tile.

        Returns:
            Vector2: The center of the entity's tile.
        """
        return self.get_center(
            Vector2(self.entity.position3.x, self.entity.position3.y)
        )

    def update(self) -> None:
        """
        Updates the camera's position if it's set to follow the entity.
        """
        if self.follows_entity:
            self.position = self.get_entity_center()

    def move(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        dx: int = 0,
        dy: int = 0,
    ) -> None:
        """
        Moves the camera to a new position or by a certain offset.

        Parameters:
            x: The new x-coordinate. Defaults to None.
            y: The new y-coordinate. Defaults to None.
            dx: The x-offset. Defaults to 0.
            dy: The y-offset. Defaults to 0.
        """
        if x is not None and y is not None:
            self.position = self.get_center(Vector2(x, y))
        else:
            tile_pos = unproject((self.position.x + dx, self.position.y + dy))
            is_x_valid, is_y_valid = self.boundary.get_boundary_validity(
                tile_pos
            )
            dx = dx if is_x_valid else 0
            dy = dy if is_y_valid else 0
            self.position.x += dx
            self.position.y += dy

    def reset_to_entity_center(self) -> None:
        """
        Resets the camera's position to the center of the entity's tile and
        enables following the entity.
        """
        self.free_roaming_enabled = False
        self.position = self.get_entity_center()
        if not self.follows_entity:
            self.follow()

    def switch_to_entity(self, new_entity: Entity[Any]) -> None:
        """
        Switch the camera to a new entity.

        Parameters:
            new_entity: The new entity to focus on.
        """
        if new_entity != self.entity:
            self.entity = new_entity
            self.position = self.get_entity_center()
            self.follows_entity = True

    def switch_to_original_entity(self) -> None:
        """
        Switch the camera back to the original entity.
        """
        self.entity = self.original_entity
        self.position = self.get_entity_center()
        self.follows_entity = True

    def handle_input(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Handles entity input events and updates the camera state accordingly."""
        if self.free_roaming_enabled:
            if event.held:
                if not self.follows_entity:
                    self.move_camera(event.button)
            elif event.pressed:
                self.move_camera(event.button)
        return None

    def move_camera(self, direction: int) -> None:
        """
        Moves the camera in a specified direction based on the input event.
        The direction is determined by the input event's button value, which can
        be one of the following: UP, DOWN, LEFT, or RIGHT.
        """
        if direction == intentions.UP:
            self.move(dy=-SPEED_UP)
        elif direction == intentions.DOWN:
            self.move(dy=SPEED_DOWN)
        elif direction == intentions.LEFT:
            self.move(dx=-SPEED_LEFT)
        elif direction == intentions.RIGHT:
            self.move(dx=SPEED_RIGHT)
