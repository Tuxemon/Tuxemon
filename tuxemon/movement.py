# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from heapq import heappop, heappush
from typing import TYPE_CHECKING

from tuxemon.db import Direction
from tuxemon.map.map import (
    dirs2,
    get_adjacent_position,
    get_coords_ext,
    get_explicit_tile_exits,
    pairs,
)
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.boundary import BoundaryChecker
    from tuxemon.db import Direction
    from tuxemon.entity.npc import NPC
    from tuxemon.event.eventmanager import EventManager
    from tuxemon.map.collision_manager import CollisionManager, CollisionMap
    from tuxemon.map.manager import MapManager
    from tuxemon.npc_manager import NPCManager
    from tuxemon.platform.input_manager import InputManager

logger = logging.getLogger(__name__)


def manhattan_distance(pos: tuple[int, int], target: tuple[int, int]) -> float:
    return abs(pos[0] - target[0]) + abs(pos[1] - target[1])


class PathfindNode:
    """Used in path finding search."""

    def __init__(
        self,
        value: tuple[int, int],
        parent: PathfindNode | None = None,
        g_cost: float = 0.0,
        h_cost: float = 0.0,
    ) -> None:
        self.parent = parent
        self.value = value
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.f_cost = self.g_cost + self.h_cost
        if self.parent:
            self.depth: int = self.parent.depth + 1
        else:
            self.depth = 0

    def get_parent(self) -> PathfindNode | None:
        return self.parent

    def set_parent(self, parent: PathfindNode) -> None:
        if parent is None or parent == self:
            raise ValueError("Parent cannot be None or the node itself.")
        logger.debug(f"Setting parent for {self.value}: {parent.value}")
        self.parent = parent
        self.depth = parent.depth + 1

    def get_value(self) -> tuple[int, int]:
        return self.value

    def get_depth(self) -> int:
        return self.depth

    def reconstruct_path(self) -> list[tuple[int, int]]:
        path = []
        current: PathfindNode | None = self
        while current:
            path.append(current.value)
            current = current.parent
        return path[:-1]

    def __str__(self) -> str:
        s = str(self.value)
        if self.parent is not None:
            s += str(self.parent)
        return s

    def __lt__(self, other: PathfindNode) -> bool:
        return (self.f_cost, self.depth) < (other.f_cost, other.depth)


class MovementManager:
    def __init__(
        self,
        event_manager: EventManager,
        input_manager: InputManager,
    ) -> None:
        self.event_manager = event_manager
        self.input_manager = input_manager
        self.wants_to_move_char: dict[str, Direction] = {}
        self.allow_char_movement: set[str] = set()

    def queue_movement(self, char_slug: str, direction: Direction) -> None:
        """Queues the movement request for a character."""
        self.wants_to_move_char[char_slug] = direction

    def move_char(self, character: NPC, direction: Direction) -> None:
        """Initiates movement of the character in the specified direction."""
        character.set_move_direction(direction)

    def stop_char(self, character: NPC) -> None:
        """Stops the character and releases movement controls."""
        self.wants_to_move_char.pop(character.slug, None)
        self.event_manager.release_controls(self.input_manager)
        character.cancel_movement()

    def unlock_controls(self, character: NPC) -> None:
        """Allows the specified character to move if movement is requested."""
        self.allow_char_movement.add(character.slug)
        if self.has_pending_movement(character):
            self.move_char(character, self.wants_to_move_char[character.slug])

    def lock_controls(self, character: NPC) -> None:
        """Prevents the specified character from moving."""
        self.allow_char_movement.discard(character.slug)

    def stop_and_reset_char(self, character: NPC) -> None:
        """Stops the character and aborts all ongoing movement actions."""
        self.wants_to_move_char.pop(character.slug, None)
        self.event_manager.release_controls(self.input_manager)
        character.abort_movement()

    def is_movement_allowed(self, character: NPC) -> bool:
        """
        Checks if movement is currently allowed for the specified character.
        """
        return character.slug in self.allow_char_movement

    def has_pending_movement(self, character: NPC) -> bool:
        """
        Checks if the specified character has a pending movement request.
        """
        return character.slug in self.wants_to_move_char


class Pathfinder:
    def __init__(
        self,
        npc_manager: NPCManager,
        map_manager: MapManager,
        collision_manager: CollisionManager,
        boundary: BoundaryChecker,
    ) -> None:
        self.npc_manager = npc_manager
        self.map_manager = map_manager
        self.collision_manager = collision_manager
        self.boundary = boundary

    def pathfind(
        self, start: tuple[int, int], dest: tuple[int, int], facing: Direction
    ) -> Sequence[tuple[int, int]] | None:
        """
        Attempts to find a path from the start position to the destination position.

        Parameters:
            start: The starting position as a tuple of (x, y) coordinates.
            dest: The destination position as a tuple of (x, y) coordinates.
            facing: The direction the character is currently facing, which influences
                pathfinding decisions.

        Returns:
            A sequence of positions representing the path if found, or None if no path
                exists.
        """
        logger.info(f"Pathfinding from {start} to {dest}.")
        open_set: list[PathfindNode] = []
        g_costs: dict[tuple[int, int], float] = {start: 0.0}
        known_nodes: set[tuple[int, int]] = set()

        start_node = PathfindNode(
            start, g_cost=0.0, h_cost=manhattan_distance(start, dest)
        )
        heappush(open_set, start_node)

        while open_set:
            current_node = heappop(open_set)
            current_pos = current_node.get_value()

            if current_pos == dest:
                logger.info(f"Destination {dest} reached.")
                return current_node.reconstruct_path()

            for neighbor_pos in self.get_exits(
                position=current_pos,
                facing=facing,
                skip_nodes=known_nodes,
            ):
                new_g_cost = g_costs[current_pos] + 1

                if new_g_cost < g_costs.get(neighbor_pos, float("inf")):
                    g_costs[neighbor_pos] = new_g_cost
                    neighbor_h_cost = manhattan_distance(neighbor_pos, dest)
                    neighbor_node = PathfindNode(
                        value=neighbor_pos,
                        parent=current_node,
                        g_cost=new_g_cost,
                        h_cost=neighbor_h_cost,
                    )
                    heappush(open_set, neighbor_node)
                    known_nodes.add(neighbor_pos)

        logger.warning(f"No path found to destination {dest}.")
        return None

    def is_valid_position(
        self, position: tuple[int, int], skip_nodes: set[tuple[int, int]]
    ) -> bool:
        """
        Checks if the given position is valid for movement.

        A position is considered valid if it is within the boundaries of the game world
        and not present in the set of nodes to skip.

        Parameters:
            position: The position to check as a tuple of (x, y) coordinates.
            skip_nodes: A set of positions that should be avoided.

        Returns:
            True if the position is valid for movement, False otherwise.
        """
        return (
            position not in skip_nodes
            and self.boundary.is_within_boundaries(position)
        )

    def get_exits(
        self,
        position: tuple[int, int],
        facing: Direction,
        collision_map: CollisionMap | None = None,
        skip_nodes: set[tuple[int, int]] | None = None,
    ) -> Sequence[tuple[int, int]]:
        """
        Determines all adjacent tiles that can be traversed from the given position.

        Parameters:
            position: The current tile coordinates (x, y).
            facing: The direction the character is currently facing.
            collision_map: Optional preloaded collision map; defaults to current map's
                collision data.
            skip_nodes: Optional set of positions to exclude from traversal.

        Returns:
            A list of adjacent tile positions that are valid for movement.
        """
        collision_map = (
            collision_map or self.collision_manager.get_collision_map()
        )
        skip_nodes = skip_nodes or set()
        logger.debug(f"[get_exits] Position: {position}, Facing: {facing}")
        logger.debug(f"[get_exits] Skip nodes: {skip_nodes}")

        tile_data = collision_map.get(position)
        exits = (
            get_explicit_tile_exits(position, tile_data, facing, skip_nodes)
            if tile_data
            else []
        )
        logger.debug(f"[get_exits] Found explicit exits: {exits}")

        adjacent_tiles = set()

        for direction, vector in dirs2.items():
            neighbor = get_adjacent_position(position, direction)
            logger.debug(
                f"[get_exits] Checking direction: {direction}, Neighbor: {neighbor}"
            )

            if self.is_tile_traversable_from(
                position, neighbor, direction, exits, collision_map, skip_nodes
            ):
                adjacent_tiles.add(neighbor)

        logger.debug(f"[get_exits] Final adjacent tiles: {adjacent_tiles}")
        return list(adjacent_tiles)

    def is_explicitly_allowed(
        self,
        neighbor: tuple[int, int],
        exits: list[tuple[float, ...]],
    ) -> bool:
        """
        Checks whether a neighbor tile is explicitly allowed based on exit rules.

        Parameters:
            neighbor: The adjacent tile to evaluate.
            exits: A list of explicitly allowed exit positions.

        Returns:
            True if no explicit exits are defined or if the neighbor is in the list;
            False otherwise.
        """
        return not exits or neighbor in exits

    def is_tile_enterable(
        self,
        neighbor: tuple[int, int],
        direction: Direction,
        collision_map: CollisionMap,
    ) -> bool:
        """
        Determines whether a tile can be entered from a given direction.

        Parameters:
            neighbor: The tile to enter.
            direction: The direction from which entry is attempted.
            collision_map: The map containing tile data and entry rules.

        Returns:
            True if the tile allows entry from the given direction; False otherwise.
        """
        try:
            tile_data = collision_map[neighbor]
        except KeyError:
            # Missing tile data implies traversable space by default.
            return True

        # Check if data exists AND if the entry rule allows it
        if tile_data is None:
            return False

        # Check if tile is blocked by entity
        if self.collision_manager.is_tile_occupied(neighbor):
            return False

        # Check if the reversed direction is in the tile's allowed entry directions.
        return pairs(direction) in tile_data.enter_from

    def is_tile_traversable_from(
        self,
        position: tuple[int, int],
        neighbor: tuple[int, int],
        direction: Direction,
        exits: list[tuple[float, ...]],
        collision_map: CollisionMap,
        skip_nodes: set[tuple[int, int]],
    ) -> bool:
        """
        Evaluates whether a neighboring tile is traversable from the current position.

        Parameters:
            position: The current tile position.
            neighbor: The adjacent tile to evaluate.
            direction: The direction of movement toward the neighbor.
            exits: A list of explicitly allowed exit positions.
            collision_map: The map containing tile data and entry rules.
            skip_nodes: A set of positions to exclude from traversal.

        Returns:
            True if the neighbor tile is traversable; False otherwise.
        """
        if not self.is_explicitly_allowed(neighbor, exits):
            logger.debug(f"[traversable] {neighbor} not in explicit exits")
            return False
        if not self.is_valid_position(neighbor, skip_nodes):
            logger.debug(
                f"[traversable] {neighbor} is invalid (boundary or skipped)"
            )
            return False
        if (position, direction) in self.map_manager.collision_lines_map:
            logger.debug(
                f"[traversable] Wall between {position} and {neighbor}"
            )
            return False
        if not self.is_tile_enterable(neighbor, direction, collision_map):
            logger.debug(
                f"[traversable] Cannot enter {neighbor} from {direction}"
            )
            return False

        logger.debug(f"[traversable] {neighbor} is traversable")
        return True

    def is_tile_traversable(
        self,
        tile_pos: tuple[int, int],
        facing: Direction,
        tile: tuple[int, int],
        ignore_collisions: bool,
    ) -> bool:
        """Checks if a tile is traversable for the given NPC."""
        if ignore_collisions:
            return True

        if tile not in self.get_exits(tile_pos, facing):
            return False

        # Check for collisions with moving entities
        _map_size = self.map_manager.map_size
        for neighbor in get_coords_ext(tile, _map_size):
            char = self.npc_manager.get_entity_pos(neighbor)
            if (
                char
                and char.moving
                and char.moverate == CONFIG.player_walkrate
                and facing != char.facing
            ):
                return False

        return True
