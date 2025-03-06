# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.boundary import BoundaryChecker
from tuxemon.db import Direction
from tuxemon.map import get_adjacent_position, get_coords_ext, pairs
from tuxemon.prepare import CONFIG

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.states.world.worldstate import CollisionMap, WorldState
logger = logging.getLogger(__name__)


class PathfindNode:
    """Used in path finding search."""

    def __init__(
        self,
        value: tuple[int, int],
        parent: Optional[PathfindNode] = None,
    ) -> None:
        self.parent = parent
        self.value = value
        if self.parent:
            self.depth: int = self.parent.depth + 1
        else:
            self.depth = 0

    def get_parent(self) -> Optional[PathfindNode]:
        return self.parent

    def set_parent(self, parent: PathfindNode) -> None:
        self.parent = parent
        self.depth = parent.depth + 1

    def get_value(self) -> tuple[int, int]:
        return self.value

    def get_depth(self) -> int:
        return self.depth

    def __str__(self) -> str:
        s = str(self.value)
        if self.parent is not None:
            s += str(self.parent)
        return s


class Pathfinder:
    def __init__(
        self, world_state: WorldState, boundary_checker: BoundaryChecker
    ) -> None:
        """
        Initializes the Pathfinder instance with the given world state.
        """
        self.world_state = world_state
        self.boundary_checker = boundary_checker

    def pathfind(
        self, start: tuple[int, int], dest: tuple[int, int]
    ) -> Optional[Sequence[tuple[int, int]]]:
        """
        Attempts to find a path from the start position to the destination position.

        Parameters:
            start: The starting position as a tuple of (x, y) coordinates.
            dest: The destination position as a tuple of (x, y) coordinates.

        Returns:
            A sequence of positions representing the path if found, or None if no path exists.
        """
        pathnode = self.pathfind_r(dest, [PathfindNode(start)], set())
        logger.info(f"Pathfinding from {start} to {dest}.")
        if pathnode:
            path = []
            while pathnode:
                path.append(pathnode.get_value())
                pathnode = pathnode.get_parent()
            logger.info(f"Path found: {path[::-1]}.")
            return path[:-1]
        else:
            character = self.world_state.get_entity_pos(start)
            if character:
                logger.error(
                    f"{character.name}'s pathfinding failed in {self.world_state.current_map.filename}."
                )
            else:
                logger.error(f"No character found at start position {start}.")
            return None

    def pathfind_r(
        self,
        dest: tuple[int, int],
        queue: list[PathfindNode],
        known_nodes: set[tuple[int, int]],
    ) -> Optional[PathfindNode]:
        """
        A recursive helper method that explores possible paths to the destination.

        Parameters:
            dest: The destination position as a tuple of (x, y) coordinates.
            queue: A deque of PathfindNode objects representing the current nodes to explore.
            known_nodes: A set of positions that have already been explored.

        Returns:
            The PathfindNode representing the destination if found, or None if no path exists.
        """
        if not queue:
            return None
        collision_map = self.world_state.get_collision_map()
        known_nodes.add(queue[0].get_value())
        logger.debug(
            f"Starting pathfinding from {queue[0].get_value()} to {dest}."
        )
        while queue:
            node = queue.pop(0)
            logger.debug(f"Checking node {node.get_value()}.")
            if node.get_value() == dest:
                logger.info(
                    f"Destination {dest} reached via {node.get_value()}."
                )
                return node
            else:
                for adj_pos in self.get_exits(
                    node.get_value(), collision_map, known_nodes
                ):
                    if adj_pos not in known_nodes:
                        known_nodes.add(adj_pos)
                        queue.append(PathfindNode(adj_pos, node))
                        logger.debug(
                            f"Adding adjacent position {adj_pos} to the queue."
                        )
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
            and self.boundary_checker.is_within_boundaries(position)
        )

    def get_exits(
        self,
        position: tuple[int, int],
        collision_map: Optional[CollisionMap] = None,
        skip_nodes: Optional[set[tuple[int, int]]] = None,
    ) -> Sequence[tuple[int, int]]:
        """
        Retrieves a list of adjacent tiles that can be moved into from the given position.

        Parameters:
            position: The original position as a tuple of (x, y) coordinates.
            collision_map: An optional mapping of collisions with entities and terrain.
            skip_nodes: A set of nodes to skip during the exit check.

        Returns:
            A sequence of adjacent and traversable tile positions.
        """
        # get tile-level and npc/entity blockers
        collision_map = collision_map or self.world_state.get_collision_map()
        skip_nodes = skip_nodes or set()
        logger.debug(f"Getting exits for position {position}.")

        # Get explicit 'continue' and 'exits' based on tile data if it exists
        exits = []
        tile_data = collision_map.get(position)
        if tile_data is not None:
            exits = self.world_state.get_explicit_tile_exits(
                position, tile_data, skip_nodes
            )
            logger.debug(f"Found explicit exits: {exits}.")
        else:
            logger.debug(
                f"No tile data found for position {position}. "
                "No explicit exits can be determined."
            )

        # get exits by checking surrounding tiles
        adjacent_tiles = set()
        for direction in [
            Direction.down,
            Direction.right,
            Direction.up,
            Direction.left,
        ]:
            neighbor = get_adjacent_position(position, direction)
            # If we have specific exits defined, make sure the neighbor is one of them
            # Also, skip this neighbor if it's in the list of nodes we want to avoid
            # We only need to check the edges since we can't go out of bounds
            if (exits and neighbor not in exits) or not self.is_valid_position(
                neighbor, skip_nodes
            ):
                logger.debug(
                    f"Skipping neighbor {neighbor} (not valid or not an exit)."
                )
                continue

            if (position, direction) in self.world_state.collision_lines_map:
                logger.debug(
                    f"Wall detected between {position} and {neighbor}."
                )
                continue

            # test if this tile has special movement handling
            # NOTE: Do not refact. into a dict.get(xxxxx, None) style check
            # NOTE: None has special meaning in this check
            try:
                tile_data = collision_map[neighbor]
            except KeyError:
                pass
            else:
                # None means tile is blocked with no specific data
                if tile_data is None:
                    continue

                try:
                    if pairs(direction) not in tile_data.enter_from:
                        continue
                except KeyError:
                    continue

            logger.debug(f"Neighbor {neighbor} is free to move into.")
            adjacent_tiles.add(neighbor)

        logger.debug(f"Adjacent tiles found: {adjacent_tiles}.")
        return list(adjacent_tiles)

    def is_tile_traversable(self, npc: NPC, tile: tuple[int, int]) -> bool:
        """Checks if a tile is traversable for the given NPC."""
        _map_size = self.world_state.map_size
        _exit = tile in self.get_exits(npc.tile_pos)

        _direction = []
        for neighbor in get_coords_ext(tile, _map_size):
            char = self.world_state.get_entity_pos(neighbor)
            if (
                char
                and char.moving
                and char.moverate == CONFIG.player_walkrate
                and npc.facing != char.facing
            ):
                _direction.append(char)

        return _exit and not _direction or npc.ignore_collisions

    def get_tile_moverate(
        self, npc: NPC, destination: tuple[int, int]
    ) -> float:
        """Gets the movement speed modifier for the given tile."""
        surface_map = self.world_state.surface_map
        tile_properties = surface_map.get(destination, {})
        rate = next(iter(tile_properties.values()), 1.0)
        _moverate = npc.moverate * rate
        return _moverate
