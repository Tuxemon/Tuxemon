# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.db import Direction, FacingMode
from tuxemon.entity.path.commands import (
    ContinueCommand,
    MovementCommand,
    PushCommand,
    RepathCommand,
    SpeedCommand,
    StopMovementCommand,
)
from tuxemon.entity.path.path_view import PathExecutionState, PathView
from tuxemon.entity.path.policies.animation import MovementAnimationPolicy
from tuxemon.entity.path.policies.reroute import ReroutePolicy
from tuxemon.entity.path.policies.tile_effects import TileEffectProcessor
from tuxemon.map.map import get_direction, get_next_tile_pos

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.map.manager import MapManager
    from tuxemon.movement import Pathfinder
    from tuxemon.npc_manager import NPCManager


logger = logging.getLogger(__name__)


class PathController:
    def __init__(
        self,
        owner: NPC,
        pathfinder: Pathfinder,
        map_manager: MapManager,
        npc_manager: NPCManager,
        tile_effects: TileEffectProcessor | None = None,
        reroute_policy: ReroutePolicy | None = None,
        animation_policy: MovementAnimationPolicy | None = None,
    ) -> None:
        self.owner = owner
        self._pathfinder = pathfinder
        self._map_manager = map_manager
        self._npc_manager = npc_manager

        self.tile_effects = tile_effects or TileEffectProcessor()
        self.reroute_policy = reroute_policy or ReroutePolicy()
        self.animation_policy = animation_policy or MovementAnimationPolicy()

        self.path = PathView([])
        self._repath_cooldown: float = 0.0
        self.pathfinding: tuple[int, int] | None = None
        self.exec = PathExecutionState()

    @property
    def move_destination(self) -> tuple[int, int] | None:
        """Only used for the char_moved condition."""
        return self.path.next()

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
            self.path = PathView(path)
            self.next_waypoint()
        else:
            # If pathfinding fails, ensure all path data is cleared.
            self.cancel_path()
            logger.warning(
                f"Could not find path for {self.owner.slug} from "
                f"{self.owner.tile_pos} to {destination}."
            )

    def update(self, dt: float) -> None:
        self._repath_cooldown = max(0.0, self._repath_cooldown - dt)

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
            if self.exec.in_progress:
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
            self.animation_policy.on_stop(self.owner)

    def set_path_and_start(self, path: list[tuple[int, int]]) -> None:
        """
        Assigns a new path to the controller and initiates movement toward the first waypoint.
        """
        self.path = PathView(path)
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

        target = self.path.next()
        assert target is not None
        move_dir = get_direction(self.owner.tile_pos, target)
        if self.owner.facing_mode == FacingMode.FOLLOW_MOVEMENT:
            direction = self.animation_policy.compute_facing(
                self.owner, target
            )
            self.animation_policy.on_face(self.owner, direction)

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
                self.animation_policy.on_step(self.owner, move_dir)
                self.exec.origin = self.owner.tile_pos
                self.exec.target = target
                self.owner.mover.move(move_dir)
                self.owner.begin_tile_exit()
            else:
                commands = self.reroute_policy.on_obstruction(
                    self.owner,
                    self._npc_manager,
                    self.pathfinding,
                    target,
                )
                for cmd in commands:
                    self.execute_command(cmd)
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
        """
        if not self.exec.in_progress:
            return

        origin = self.exec.origin
        target = self.exec.target
        assert origin is not None and target is not None

        if self.owner.mover.has_reached_next_tile(origin, target):
            self.owner.complete_tile_entry(target)
            self.path.consume()
            self.exec.reset()
            tile = self._map_manager.collision_map.get(self.owner.tile_pos)
            commands = self.tile_effects.get_effects(
                tile,
                self.owner,
                self.path,
            )
            for cmd in commands:
                self.execute_command(cmd)
            if self.path:
                self.next_waypoint()

    def move_one_tile(self, direction: Direction) -> None:
        target = get_next_tile_pos(self.owner.tile_pos, direction)
        self.path.push(target)

    def move_multiple_tiles(self, direction: Direction, strength: int) -> None:
        """
        Attempts to move the entity multiple tiles in the specified direction,
        up to the given strength.

        This method checks tile-by-tile whether movement is allowed using the
        pathfinder's exit logic.
        If a tile is blocked, movement stops at the last valid position. The
        resulting path is reversed before being appended to ensure that the
        next waypoint is always the immediate neighbor, since movement logic
        expects self.path.next() to be adjacent to the current position.

        Parameters:
            direction: The direction in which to move.
            strength: The maximum number of tiles to attempt moving through.
        """
        if strength <= 0:
            return

        if self.owner.facing_mode == FacingMode.FOLLOW_MOVEMENT:
            self.animation_policy.on_face(self.owner, direction)

        origin = self.path.next()
        if origin is None:
            origin = self.owner.tile_pos
        steps: list[tuple[int, int]] = []

        for _ in range(strength):
            candidate = get_next_tile_pos(origin, direction)

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
            self.path.extend_reversed(steps)
            self.exec.origin = self.owner.tile_pos
            logger.debug(
                f"Final path (last is next): {self.path} | origin={self.exec.origin}"
            )
            self.next_waypoint()

    def cancel_path(self) -> None:
        """
        Clears all active pathfinding data and stops the NPC's movement.

        This method removes the NPC's current path and resets pathfinding
        related attributes, ensuring no further automatic movement occurs.
        """
        self.path = PathView([])
        self.pathfinding = None
        self.exec.reset()

    def cancel_movement(self) -> None:
        """
        Stops the NPC's movement and adjusts pathfinding logic if necessary.

        If the NPC is currently following a path but hasn't reached the
        destination, it retains the last waypoint to avoid abrupt stopping.
        Otherwise, all movement is halted and pathfinding is cleared.
        """
        at_origin = (
            self.exec.origin is not None
            and self.owner.position == self.exec.origin
        )
        mid_movement = self.path and self.owner.moving

        if at_origin:
            # Movement started but hasn't progressed
            self.abort_movement(preserve_position=True)
            return

        if mid_movement:
            # Keep last waypoint so NPC finishes the tile cleanly
            last = self.path.next()
            self.path = PathView([last] if last else [])
            self.pathfinding = None
            self.owner.mover.set_move_direction()
            return

        # Default: fully stop and clear everything
        self.abort_movement()

    def abort_movement(self, preserve_position: bool = False) -> None:
        """
        Safely halts all movement-related actions for the NPC.

        This method ensures that the NPC stops moving, cancels any
        active pathfinding, and resets its movement direction. If
        `preserve_position` is True, the NPC's current tile position
        is retained; otherwise, it reverts to its last recorded origin.
        """
        if not preserve_position and self.exec.origin is not None:
            self.owner.complete_tile_entry(self.exec.origin)
        self.owner.mover.set_move_direction()
        self.owner.stop_moving()
        self.cancel_path()

    def execute_command(self, cmd: MovementCommand) -> None:
        """
        Central dispatcher that applies policy decisions to controller/owner state.
        """
        if isinstance(cmd, PushCommand):
            self.move_multiple_tiles(cmd.direction, cmd.strength)
        elif isinstance(cmd, SpeedCommand):
            self.owner.mover.set_moverate_modifier(cmd.modifier)
        elif isinstance(cmd, ContinueCommand):
            self.move_one_tile(cmd.direction)
        elif isinstance(cmd, RepathCommand):
            self._repath_cooldown = cmd.cooldown
            if cmd.immediate:
                self.start_path(cmd.destination)
        elif isinstance(cmd, StopMovementCommand):
            self.owner.stop_moving()
