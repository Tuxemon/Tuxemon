# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.math import Vector2
from tuxemon.platform.const import intentions
from tuxemon.session import local_session

if TYPE_CHECKING:
    from tuxemon.npc import NPC
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


class Camera:
    """
    A camera class that follows a player object in a game or simulation.

    Attributes:
        player: The player object that the camera follows.
        tile_size: The size of the tiles in the game world.
        position: The current position of the camera.
        follows_player: Whether the camera is currently following the player.
        original_player: The original player object that the camera follows.
    """

    def __init__(self, player: NPC):
        """
        Initializes the camera with a reference to a player object.

        Parameters:
            player: The player object that the camera follows.
        """
        self.player = player
        self.original_player = player
        self.tile_size = prepare.TILE_SIZE
        self.position = self.get_player_center()
        self.follows_player = True
        self.free_roaming_enabled = False

    def follow(self) -> None:
        """
        Start the camera following the current player.
        """
        self.follows_player = True

    def unfollow(self) -> None:
        """
        Stop the camera from following the current player.
        """
        self.follows_player = False

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

    def get_player_center(self) -> Vector2:
        """
        Returns the center of the player's tile.

        Returns:
            Vector2: The center of the player's tile.
        """
        return self.get_center(
            Vector2(self.player.position3.x, self.player.position3.y)
        )

    def update(self) -> None:
        """
        Updates the camera's position if it's set to follow the player.
        """
        if self.follows_player:
            self.position = self.get_player_center()

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
            new_x = self.position.x + dx
            new_y = self.position.y + dy
            map_size = local_session.client.map_size
            min_x, _ = project((0, 0))
            max_x, _ = project((map_size[0], 0))
            _, min_y = project((0, 0))
            _, max_y = project((0, map_size[1]))

            if new_x < min_x:
                dx = 0
            elif new_x > max_x:
                dx = 0

            if new_y < min_y:
                dy = 0
            elif new_y > max_y:
                dy = 0

            self.position.x += dx
            self.position.y += dy

    def move_up(self, speed: int = SPEED_UP) -> None:
        """Moves the camera up by a certain speed."""
        self.move(dy=-speed)

    def move_down(self, speed: int = SPEED_DOWN) -> None:
        """Moves the camera down by a certain speed."""
        self.move(dy=speed)

    def move_left(self, speed: int = SPEED_LEFT) -> None:
        """Moves the camera left by a certain speed."""
        self.move(dx=-speed)

    def move_right(self, speed: int = SPEED_RIGHT) -> None:
        """Moves the camera right by a certain speed."""
        self.move(dx=speed)

    def reset_to_player_center(self) -> None:
        """
        Resets the camera's position to the center of the player's tile and
        enables following the player.
        """
        self.free_roaming_enabled = False
        self.position = self.get_player_center()
        if not self.follows_player:
            self.follow()

    def switch_to_player(self, new_player: NPC) -> None:
        """
        Switch the camera to a new player.

        Parameters:
            new_player: The new player to focus on.
        """
        if new_player != self.player:
            self.player = new_player
            self.position = self.get_player_center()
            self.follows_player = True

    def switch_to_original_player(self) -> None:
        """
        Switch the camera back to the original player.
        """
        self.player = self.original_player
        self.position = self.get_player_center()
        self.follows_player = True

    def handle_input(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Handles player input events and updates the camera state accordingly."""
        if self.free_roaming_enabled:
            if event.held:
                if not self.follows_player:
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
            self.move_up()
        elif direction == intentions.DOWN:
            self.move_down()
        elif direction == intentions.LEFT:
            self.move_left()
        elif direction == intentions.RIGHT:
            self.move_right()
