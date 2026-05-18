# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon.math import Vector2
from tuxemon.platform.const import intentions
from tuxemon.prepare import DisplayContext

if TYPE_CHECKING:
    from tuxemon.boundary import BoundaryChecker
    from tuxemon.entity.entity import Entity
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


def project(
    context: DisplayContext, position: Sequence[float]
) -> tuple[int, int]:
    ts = context.tile_size
    return (
        int(position[0] * ts[0]),
        int(position[1] * ts[1]),
    )


def unproject(
    context: DisplayContext, position: Sequence[float]
) -> tuple[int, int]:
    ts = context.tile_size
    return (
        int(position[0] / ts[0]),
        int(position[1] / ts[1]),
    )


class CameraController:
    """Handles directional input for camera movement during free roaming."""

    def __init__(self, camera: Camera):
        """Initializes the controller with a reference to the camera."""
        self.camera = camera
        self.enabled: bool = True
        self.speed: int = 7

    def handle_input(self, input_event: PlayerInput) -> PlayerInput | None:
        """
        Processes input events to move the camera if roaming is enabled.

        Returns the input event if processed, otherwise None.
        """
        if not self.enabled or not self.camera.free_roaming_enabled:
            return None

        if input_event.held or input_event.pressed:
            self._apply_direction(input_event.button)
            return input_event

        return None

    def _apply_direction(self, direction: int) -> None:
        """
        Maps directional input to corresponding camera movement actions,
        using the instance speed.
        """
        dx = 0
        dy = 0

        if direction == intentions.UP:
            dy = -self.speed
        elif direction == intentions.DOWN:
            dy = self.speed
        elif direction == intentions.LEFT:
            dx = -self.speed
        elif direction == intentions.RIGHT:
            dx = self.speed

        if dx != 0 or dy != 0:
            self.camera.move(dx=dx, dy=dy)

    def set_roaming_speed(self, value: int) -> None:
        """Sets the new roaming speed for the camera controller."""
        self.speed = value

    def is_roaming_enabled(self) -> bool:
        """Returns True if the camera's free roaming is enabled."""
        return self.camera.free_roaming_enabled

    def set_enabled(self, value: bool) -> None:
        """Enables or disables the controller."""
        self.enabled = value


class CameraManager:
    """Manages multiple cameras and delegates input and updates to the active one."""

    def __init__(self) -> None:
        self.cameras: dict[str, Camera] = {}
        self.active_camera: Camera | None = None
        self.controller: CameraController | None = None

    def add_camera(self, name: str, camera: Camera) -> None:
        """Adds a camera to the manager and sets it active if none is selected."""
        self.cameras[name] = camera
        if self.active_camera is None:
            self.set_active_camera(name)

    def remove_camera(self, name: str) -> None:
        """Removes a camera by name. Clears active camera and controller if it was active."""
        if name in self.cameras:
            removed = self.cameras.pop(name)

            if self.active_camera is removed:
                self.active_camera = None
                self.controller = None
        else:
            raise ValueError("Camera not managed by this CameraManager.")

    def reset(self) -> None:
        """Resets the camera manager to its initial state."""
        self.cameras.clear()
        self.active_camera = None
        self.controller = None

    def set_active_camera(self, name: str) -> None:
        """Sets the specified camera as active and assigns its controller."""
        if name in self.cameras:
            self.active_camera = self.cameras[name]
            self.controller = CameraController(self.active_camera)
        else:
            raise ValueError("Camera not managed by this CameraManager.")

    def update(self, dt: float) -> None:
        """Updates the active camera with the given time delta."""
        if self.active_camera:
            self.active_camera.update(dt)

    def handle_input(self, event: PlayerInput) -> PlayerInput | None:
        """Delegates input handling to the active camera's controller."""
        if self.controller:
            return self.controller.handle_input(event)
        return None

    def get_active_camera(self) -> Camera | None:
        """Returns the currently active camera, if any."""
        return self.active_camera


class CameraView:
    """Represents the camera's viewport, position, and zoom level."""

    def __init__(self, context: DisplayContext):
        """Initializes the view with a tile size and default position."""
        self.context = context
        self.tile_size = context.tile_size
        self.screen_size = context.rect.size
        self.position = Vector2(0, 0)

    def set_position(self, x: float, y: float) -> None:
        """Centers the view on the specified world coordinates."""
        self.position = self.get_center(Vector2(x, y))

    def get_center(self, position: Vector2) -> Vector2:
        """Calculates the center point of the view based on tile size."""
        cx, cy = project(self.context, position)
        return Vector2(
            cx + self.tile_size[0] // 2, cy + self.tile_size[1] // 2
        )

    def move(self, dx: int = 0, dy: int = 0) -> None:
        """Moves the view by the specified offset in pixels."""
        self.position.x += dx
        self.position.y += dy

    def get_size(self) -> tuple[int, int]:
        """
        Returns the viewport size in pixels, adjusted for the current zoom level.
        """
        width = self.screen_size[0]
        height = self.screen_size[1]
        return width, height


class CameraTracker:
    """Manages camera tracking and smooth transitions to target positions."""

    def __init__(self, view: CameraView, entity: Entity):
        """
        Initializes the tracker with a camera view and target entity.
        """
        self.view = view
        self.entity = entity
        self.original_entity = entity
        self.follows_entity: bool = True
        self.is_moving_smoothly: bool = False
        self.pending_follow: bool = False
        self.target_position = Vector2(0, 0)
        self.transition_speed: float = 5.0

    def update(self, dt: float) -> Vector2:
        """
        Updates camera position based on entity tracking or smooth movement.
        """
        if self.is_moving_smoothly:
            self._update_smooth_transition(dt)
        elif self.follows_entity:
            pos = Vector2(self.entity.position.x, self.entity.position.y)
            self.view.position = self.view.get_center(pos)
        return Vector2(0, 0)

    def move_smoothly_to(self, target: Vector2, duration: float) -> None:
        """
        Initiates a smooth transition to the specified target position.
        """
        self.target_position = self.view.get_center(target)
        distance = self._get_distance(self.view.position, self.target_position)
        self.transition_speed = distance / duration
        self.is_moving_smoothly = True

    def _update_smooth_transition(self, dt: float) -> None:
        """
        Performs frame-by-frame interpolation toward the target position.
        """
        dx = self.target_position.x - self.view.position.x
        dy = self.target_position.y - self.view.position.y
        distance = self._get_distance(self.view.position, self.target_position)
        step = self.transition_speed * dt

        if step >= distance:
            self.view.position = self.target_position
            self.is_moving_smoothly = False
            if self.pending_follow:
                self.follows_entity = True
                self.pending_follow = False
        else:
            self.view.position.x += step * (dx / distance)
            self.view.position.y += step * (dy / distance)

    def set_entity(self, entity: Entity, reset: bool = False) -> None:
        """
        Sets the tracker to follow the given entity, optionally snapping
        immediately.
        """
        self.entity = entity
        self.follows_entity = True
        if reset:
            pos = Vector2(entity.position.x, entity.position.y)
            self.view.position = self.view.get_center(pos)

    def _get_distance(self, pos1: Vector2, pos2: Vector2) -> float:
        """Calculates the Euclidean distance between two positions."""
        return math.hypot(pos2.x - pos1.x, pos2.y - pos1.y)


class CameraEffects:
    """Handles visual effects applied to the camera view."""

    def __init__(self, view: CameraView):
        """Initializes the effects system with a reference to the camera view."""
        self.view = view
        self.shake_intensity: float = 0.0
        self.shake_duration: float = 0.0

    def shake(self, intensity: float, duration: float) -> None:
        """Starts a shake effect with given intensity and duration."""
        self.shake_intensity = intensity
        self.shake_duration = duration

    def update(self, dt: float) -> None:
        """Applies shake jitter to the view and updates remaining duration."""
        if self.shake_duration > 0:
            jitter_x = random.uniform(
                -self.shake_intensity, self.shake_intensity
            )
            jitter_y = random.uniform(
                -self.shake_intensity, self.shake_intensity
            )
            self.view.position += Vector2(jitter_x, jitter_y)
            self.shake_duration -= dt
        else:
            self.shake_duration = 0.0


class Camera:
    def __init__(
        self,
        entity: Entity,
        boundary: BoundaryChecker,
        context: DisplayContext,
    ):
        self.view = CameraView(context)
        self.tracker = CameraTracker(self.view, entity)
        self.effects = CameraEffects(self.view)
        self.context = context
        self.boundary = boundary
        self.free_roaming_enabled: bool = False

    def update(self, dt: float) -> None:
        """Updates the camera tracker, applies movement, and handles visual effects."""
        move_intent = self.tracker.update(dt)

        if move_intent.x != 0 or move_intent.y != 0:
            self.move(dx=int(move_intent.x), dy=int(move_intent.y))

        self.effects.update(dt)

    def get_viewport(self) -> Rect:
        """Returns the visible area of the game world as a Rect."""
        center = Vector2(self.get_position())
        width, height = self.view.get_size()
        offset = Vector2(width // 2, height // 2)
        top_left = center - offset
        return Rect(int(top_left.x), int(top_left.y), int(width), int(height))

    def get_viewport_center(self) -> Vector2:
        """Returns the center of the viewport as a Vector2."""
        return Vector2(self.get_viewport().center)

    def move(self, dx: int = 0, dy: int = 0) -> None:
        """Moves the camera by a specified offset, constrained by boundary validity."""
        tile_pos = unproject(
            self.context,
            (self.view.position.x + dx, self.view.position.y + dy),
        )
        is_x_valid, is_y_valid = self.boundary.get_boundary_validity(tile_pos)
        if is_x_valid:
            self.view.position.x += dx
        if is_y_valid:
            self.view.position.y += dy

    def is_following(self) -> bool:
        """Returns whether the camera is currently following its target entity."""
        return self.tracker.follows_entity

    def set_position(self, x: float, y: float) -> None:
        """Sets the camera's position directly to the specified coordinates."""
        self.view.set_position(x, y)

    def follow(self) -> None:
        """Enables camera tracking of the target entity."""
        self.tracker.follows_entity = True

    def unfollow(self) -> None:
        """Disables camera tracking, allowing free movement."""
        self.tracker.follows_entity = False

    def shake(self, intensity: float, duration: float) -> None:
        """Applies a shake effect to the camera with given intensity and duration."""
        self.effects.shake(intensity, duration)

    def smooth_reset_to_entity_center(self, duration: float) -> None:
        """Smoothly transitions the camera to center on the entity over a specified duration."""
        position_2d = Vector2(
            self.tracker.entity.position.x, self.tracker.entity.position.y
        )
        self.tracker.move_smoothly_to(position_2d, duration)
        self.tracker.pending_follow = True

    def switch_entity(
        self, new_entity: Entity | None = None, reset: bool = False
    ) -> None:
        """
        Switches the camera's target to a new entity, or restores the original
        entity if none is given.

        Parameters:
            new_entity: The entity to follow. If None, the camera resets to the
                original entity.
            reset: If True, immediately centers the camera on the entity.
        """
        target = (
            new_entity
            if new_entity is not None
            else self.tracker.original_entity
        )
        self.tracker.set_entity(target, reset)

    def reset_to_entity_center(self) -> None:
        """Immediately centers the camera on the entity and disables free roaming."""
        self.free_roaming_enabled = False
        self.tracker.follows_entity = True
        position_2d = Vector2(
            self.tracker.entity.position.x, self.tracker.entity.position.y
        )
        self.view.position = self.view.get_center(position_2d)

    def move_smoothly_to(self, x: float, y: float, duration: float) -> None:
        """Smoothly moves the camera to the specified coordinates over a given duration."""
        self.tracker.move_smoothly_to(Vector2(x, y), duration)

    def get_position(self) -> Vector2:
        """Returns the current position of the camera view."""
        return self.view.position
