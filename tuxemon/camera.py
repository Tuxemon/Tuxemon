# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import prepare
from tuxemon.math import Vector2
from tuxemon.platform.const import intentions

if TYPE_CHECKING:
    from tuxemon.boundary import BoundaryChecker
    from tuxemon.entity import Entity
    from tuxemon.platform.events import PlayerInput

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


class CameraManager:
    def __init__(self) -> None:
        """
        Initializes the CameraManager with an empty list of cameras and
        no active camera or input handler.
        """
        self.cameras: list[Camera] = []
        self.active_camera: Optional[Camera] = None
        self.input_handler: Optional[CameraInputHandler] = None

    def add_camera(self, camera: Camera) -> None:
        """Adds a new camera to the manager.

        If there is no active camera, the newly added camera is set as the
        active camera.

        Parameters:
            camera: The camera instance to be added.
        """
        self.cameras.append(camera)
        if self.active_camera is None:
            self.set_active_camera(camera)

    def set_active_camera(self, camera: Camera) -> None:
        """
        Sets the specified camera as the active camera.
        This also initializes the input handler for the active camera.

        Parameters:
            camera: The camera instance to be set as active.

        Raises:
            ValueError: If the specified camera is not in the list of
            managed cameras.
        """
        if camera in self.cameras:
            self.active_camera = camera
            self.input_handler = CameraInputHandler(camera)
        else:
            raise ValueError("Camera not managed by this CameraManager.")

    def update(self) -> None:
        """
        Updates the active camera, if one is set.

        This method should be called regularly to ensure the active camera's
        state is updated.
        """
        if self.active_camera:
            self.active_camera.update()

    def handle_input(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Handles player input events through the active camera's input handler.

        Parameters:
            event: The input event to be handled.

        Returns:
            The result of the input handling, or None if no input handler is set.
        """
        if self.input_handler:
            return self.input_handler.handle_input(event)
        return None

    def get_active_camera(self) -> Optional[Camera]:
        """
        Returns the currently active camera.

        Returns:
            The active camera instance, or None if no camera is active.
        """
        return self.active_camera


class CameraInputHandler:
    def __init__(self, camera: Camera):
        self.camera = camera

    def handle_input(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Handles entity input events and updates the camera state accordingly.

        Returns the PlayerInput event if processed, otherwise returns None.
        """
        if self.camera.free_roaming_enabled:
            if event.held or event.pressed:
                self.process_direction(event.button)
                return event
        return None

    def process_direction(self, direction: int) -> None:
        """
        Moves the camera in a specified direction based on the input event.
        The direction is determined by the input event's button value, which can
        be one of the following: UP, DOWN, LEFT, or RIGHT.
        """
        if direction == intentions.UP:
            self.camera.move_up()
        elif direction == intentions.DOWN:
            self.camera.move_down()
        elif direction == intentions.LEFT:
            self.camera.move_left()
        elif direction == intentions.RIGHT:
            self.camera.move_right()


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

    FRAME_RATE: int = 60

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
        self.shake_intensity = 0.0
        self.shake_duration = 0.0

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
        self.handle_shake()

    def set_position(self, x: float, y: float) -> None:
        """
        Moves the camera to a new position.

        Parameters:
            x: The new x-coordinate. Defaults to None.
            y: The new y-coordinate. Defaults to None.
        """
        self.position = self.get_center(Vector2(x, y))

    def move(self, dx: int = 0, dy: int = 0) -> None:
        """
        Moves the camera by a certain offset.

        Parameters:
            dx: The x-offset. Defaults to 0.
            dy: The y-offset. Defaults to 0.
        """
        if dx == 0 and dy == 0:
            return

        tile_pos = unproject((self.position.x + dx, self.position.y + dy))
        is_x_valid, is_y_valid = self.boundary.get_boundary_validity(tile_pos)

        if is_x_valid:
            self.position.x += dx
        if is_y_valid:
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

    def move_up(self) -> None:
        self.move(dy=-SPEED_UP)

    def move_down(self) -> None:
        self.move(dy=SPEED_DOWN)

    def move_left(self) -> None:
        self.move(dx=-SPEED_LEFT)

    def move_right(self) -> None:
        self.move(dx=SPEED_RIGHT)

    def shake(self, intensity: float, duration: float) -> None:
        """
        Initiates a shake effect with the specified intensity and duration.

        Parameters:
            intensity: The magnitude of the shake effect.
            duration: The length of time (in seconds) that the shake effect should last.
        """
        self.shake_intensity = intensity
        self.shake_duration = duration

    def handle_shake(self) -> None:
        """
        Applies the shake effect to the camera's position if the shake duration is active.
        """
        if self.shake_duration > 0:
            original_position = Vector2(self.position.x, self.position.y)
            self.position.x += random.uniform(
                -self.shake_intensity, self.shake_intensity
            )
            self.position.y += random.uniform(
                -self.shake_intensity, self.shake_intensity
            )

            self.shake_duration -= 1 / self.FRAME_RATE
            if self.shake_duration <= 0:
                self.shake_duration = 0
                self.position = original_position
