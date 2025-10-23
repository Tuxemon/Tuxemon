# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable
from math import hypot
from typing import TYPE_CHECKING, Optional

from tuxemon.db import Direction
from tuxemon.map.map import dirs2, get_direction, proj
from tuxemon.math import Vector2
from tuxemon.tools import vector2_to_tile_pos

if TYPE_CHECKING:
    from tuxemon.map.map_manager import MapManager
    from tuxemon.movement import Pathfinder
    from tuxemon.npc import NPC
    from tuxemon.npc_manager import NPCManager


logger = logging.getLogger(__name__)


def tile_distance(tile0: Iterable[float], tile1: Iterable[float]) -> float:
    x0, y0 = tile0
    x1, y1 = tile1
    return hypot(x1 - x0, y1 - y0)


class PathController:
    def __init__(
        self,
        owner: NPC,
        pathfinder: Pathfinder,
        map_manager: MapManager,
        npc_manager: NPCManager,
    ) -> None:
        self.owner = owner
        self._pathfinder = pathfinder
        self._map_manager = map_manager
        self._npc_manager = npc_manager
        self._repath_cooldown: float = 0.0
        self.path: list[tuple[int, int]] = []
        self.pathfinding: Optional[tuple[int, int]] = None
        self.path_origin: Optional[tuple[int, int]] = None

    @property
    def move_destination(self) -> Optional[tuple[int, int]]:
        """Only used for the char_moved condition."""
        return self.path[-1] if self.path else None

    def start_path(self, destination: tuple[int, int]) -> None:
        """
        Find a path and also start it.

        If asked to pathfind, an NPC will pathfind until it:
        * reaches the destination
        * NPC.cancel_movement() is called

        If blocked, the NPC will wait until it is able to move.

        Queries the world for a valid path.

        Parameters:
            destination: Desired final position.
        """
        self.pathfinding = destination
        path = self._pathfinder.pathfind(
            self.owner.tile_pos, destination, self.owner.facing
        )
        if path:
            self.path = list(path)
            self.next_waypoint()
        else:
            # If pathfinding fails, ensure all path data is cleared.
            self.cancel_path()
            logger.warning(
                f"Could not find path for {self.owner.slug} from "
                f"{self.owner.tile_pos} to {destination}."
            )

    def update(self, time_delta: float) -> None:
        self._repath_cooldown = max(0.0, self._repath_cooldown - time_delta)

        if self.path or self.owner.move_direction:
            self.process_movement()

    def process_movement(self) -> None:
        """
        Manages NPC movement logic, handling pathfinding, waypoint progression,
        and obstructions.

        This method ensures smooth movement by:
        - Initiating pathfinding if needed.
        - Progressing through waypoints.
        - Responding to blocked paths or missing destinations.
        - Handling direct movement requests when no path exists.

        If movement is blocked or invalid, appropriate cancellation routines
        are triggered.
        """
        if self.pathfinding and not self.path:
            if self._repath_cooldown <= 0.0:
                self.start_path(self.pathfinding)
            return

        if self.path:
            if self.path_origin:
                self.check_waypoint()
            else:
                self.next_waypoint()

        # Direct movement handling
        if self.owner.move_direction:
            if self.path and not self.owner.moving:
                self.cancel_path()

            if not self.path:
                self.move_one_tile(self.owner.move_direction)
                self.next_waypoint()

        if not self.path:
            self.cancel_movement()
            self.owner.sprite_controller.stop_animation()

    def set_path_and_start(self, path: list[tuple[int, int]]) -> None:
        """
        Assigns a new path to the controller and initiates movement toward the first waypoint.
        """
        self.path = path
        logger.debug(f"Path set for {self.owner.slug}: {self.path}")
        self.next_waypoint()

    def next_waypoint(self) -> None:
        """
        Take the next step of the path, stop if way is blocked.

        * This must be called after a path is set
        * Not needed to be called if existing path is modified
        * If the next waypoint is blocked, the waypoint will be removed
        """
        if not self.path:
            return

        target = self.path[-1]
        direction = get_direction(proj(self.owner.position), target)
        self.owner.set_facing(direction)

        try:
            if self._pathfinder.is_tile_traversable(
                self.owner.tile_pos,
                self.owner.facing,
                target,
                self.owner.ignore_collisions,
            ):
                # Surfanim suffers from significant clock drift, causing
                # timing inconsistencies. Even after completing one animation
                # cycle, the timing can become inaccurate. This drift results
                # in walking steps misaligning with tile positions, with
                # certain frames lasting only a single game frame.
                # Using `play` to initiate each tile transition helps reset
                # the surfanim timer, keeping walking animation frames in sync.
                # However, occasional desynchronization still occurs.
                # To fully resolve this issue, the game will eventually need
                # a dedicated global clock—not reliant on wall time—to eliminate
                # visual glitches and ensure frame accuracy.
                self.owner.sprite_controller.play_animation()
                self.path_origin = self.owner.tile_pos
                self.owner.mover.move(self.owner.mover.current_direction)
                self.owner.remove_collision()
            else:
                self.owner.stop_moving()
                self.handle_obstruction(target)
        except Exception as e:
            logger.error(
                f"Error in next_waypoint for {self.owner.slug}: {e}",
                exc_info=True,
            )
            self.cancel_path()

    def check_waypoint(self) -> None:
        """
        Check if the waypoint is reached and sets new waypoint if so.

        * For most accurate speed, tests distance traveled.
        * Doesn't verify the target position, just distance
        * Assumes once waypoint is set, direction doesn't change
        * Honors continue tiles
        """
        if not self.path_origin:
            return

        target = self.path[-1]
        expected = tile_distance(self.path_origin, target)
        traveled = tile_distance(proj(self.owner.position), self.path_origin)
        if traveled >= expected:
            self.owner.set_position(target)
            self.path.pop()
            self.path_origin = None
            self._apply_tile_effects()
            self.check_continue()
            if self.path:
                self.next_waypoint()

    def check_continue(self) -> None:
        try:
            tile = self._map_manager.collision_map[self.owner.tile_pos]
            if tile and tile.endure:
                # Use self.owner.facing if the tile allows multiple directions (> 1).
                if len(tile.endure) > 1:
                    _direction = self.owner.facing
                # Otherwise, it must be the single required direction (len == 1).
                else:
                    _direction = tile.endure[0]

                self.move_one_tile(_direction)
            else:
                pass
        except (KeyError, TypeError):
            pass

    def _apply_tile_effects(self) -> None:
        try:
            tile = self._map_manager.collision_map.get(self.owner.tile_pos)
            if tile is None:
                return

            if tile.push_effect:
                self.move_multiple_tiles(
                    direction=tile.push_effect.direction,
                    strength=tile.push_effect.strength,
                )

            if tile.speed_modifier:
                self.owner.set_moverate_modifier(tile.speed_modifier)
        except (KeyError, TypeError):
            pass

    def _get_next_tile_pos(
        self, origin: tuple[int, int], direction: Direction
    ) -> tuple[int, int]:
        """Calculates the target tile position one step away from the origin."""
        target_vec = Vector2(origin) + dirs2[direction]
        return vector2_to_tile_pos(target_vec)

    def move_one_tile(self, direction: Direction) -> None:
        target = self._get_next_tile_pos(self.owner.tile_pos, direction)
        self.path.append(target)

    def move_multiple_tiles(self, direction: Direction, strength: int) -> None:
        """
        Attempts to move the entity multiple tiles in the specified direction,
        up to the given strength.

        This method checks tile-by-tile whether movement is allowed using the
        pathfinder's exit logic.
        If a tile is blocked, movement stops at the last valid position. The
        resulting path is reversed before being appended to ensure that the
        next waypoint is always the immediate neighbor, since movement logic
        expects self.path[-1] to be adjacent to the current position.

        Parameters:
            direction: The direction in which to move.
            strength: The maximum number of tiles to attempt moving through.
        """
        self.owner.set_facing(direction)

        origin = self.path[-1] if self.path else self.owner.tile_pos
        steps = []

        for _ in range(strength):
            candidate = self._get_next_tile_pos(origin, direction)

            if candidate == origin:
                logger.debug(f"Skipping duplicate tile: {candidate}")
                continue

            exits = self._pathfinder.get_exits(origin, direction)
            logger.debug(
                f"Valid exits from {origin} facing {direction}: {exits}"
            )
            if candidate not in exits:
                logger.debug(
                    f"Tile blocked: {candidate} from {origin} facing {direction}"
                )
                break

            steps.append(candidate)
            origin = candidate

        if steps:
            self.path.extend(reversed(steps))
            self.path_origin = self.owner.tile_pos
            logger.debug(
                f"Final path (last is next): {self.path} | path_origin={self.path_origin}"
            )
            self.next_waypoint()

    def cancel_path(self) -> None:
        """
        Clears all active pathfinding data and stops the NPC's movement.

        This method removes the NPC's current path and resets pathfinding
        related attributes, ensuring no further automatic movement occurs.
        """
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self) -> None:
        """
        Stops the NPC's movement and adjusts pathfinding logic if necessary.

        If the NPC is currently following a path but hasn't reached the
        destination, it retains the last waypoint to avoid abrupt stopping.
        Otherwise, all movement is halted and pathfinding is cleared.
        """
        if proj(self.owner.position) == self.path_origin:
            self.abort_movement(preserve_position=True)
        elif self.path and self.owner.moving:
            self.path = [self.path[-1]]
            self.pathfinding = None
            self.owner.set_move_direction()
        else:
            self.abort_movement()

    def abort_movement(self, preserve_position: bool = False) -> None:
        """
        Safely halts all movement-related actions for the NPC.

        This method ensures that the NPC stops moving, cancels any
        active pathfinding, and resets its movement direction. If
        `preserve_position` is True, the NPC's current tile position
        is retained; otherwise, it reverts to its last recorded origin.
        """
        if not preserve_position and self.path_origin is not None:
            self.owner.tile_pos = self.path_origin
        self.owner.set_move_direction()
        self.owner.stop_moving()
        self.cancel_path()

    def handle_obstruction(self, target: tuple[int, int]) -> None:
        if self.pathfinding:
            npc = self._npc_manager.get_entity_pos(self.pathfinding)
            if npc:
                logger.info(
                    f"{npc.slug} obstructing {self.owner.slug}, recalculating path."
                )
                self._repath_cooldown = 0.5
                self.start_path(self.pathfinding)
            else:
                logger.warning(
                    f"{self.owner.slug} could not proceed to {self.pathfinding} due to obstruction. "
                    "Consider splitting pathfinding or postponing movement."
                )
                self._repath_cooldown = 1.0
                self.owner.stop_moving()
        else:
            logger.debug(
                f"{self.owner.slug} faced obstruction at {target}. Movement stopped."
            )
