# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Mapping, Sequence
from itertools import product
from math import atan2, pi
from typing import TYPE_CHECKING, Optional, TypeVar, Union

from tuxemon.camera.camera import project
from tuxemon.compat.rect import ReadOnlyRect
from tuxemon.db import Direction, Orientation
from tuxemon.math import Vector2, Vector3
from tuxemon.tools import round_to_divisible

if TYPE_CHECKING:
    from tuxemon.map.map_region import RegionProperties
    from tuxemon.map.map_tuxemon import AbstractMap

logger = logging.getLogger(__name__)

RectTypeVar = TypeVar("RectTypeVar", bound=ReadOnlyRect)


# direction => vector
dirs3: Mapping[Direction, Vector3] = {
    Direction.up: Vector3(0, -1, 0),
    Direction.down: Vector3(0, 1, 0),
    Direction.left: Vector3(-1, 0, 0),
    Direction.right: Vector3(1, 0, 0),
}
dirs2: Mapping[Direction, Vector2] = {
    Direction.up: Vector2(0, -1),
    Direction.down: Vector2(0, 1),
    Direction.left: Vector2(-1, 0),
    Direction.right: Vector2(1, 0),
}
# just the first letter of the direction => vector
short_dirs = {d[0]: dirs2[d] for d in dirs2}


def translate_short_path(
    path: str,
    position: tuple[int, int] = (0, 0),
) -> Generator[tuple[int, int], None, None]:
    """
    Translate condensed path strings into coordinate pairs.

    Uses a string of U D L R characters; Up Down Left Right.
    Passing a position will make the path relative to that point.

    Parameters:
        path: String of path directions; ie "uldr".
        position: Starting point of the path.

    Yields:
        Positions in the path.
    """
    position_vec = Vector2(*position)
    for char in path.lower():
        position_vec += short_dirs[char]
        yield (int(position_vec.x), int(position_vec.y))


def simple_path(
    origin: tuple[int, int], direction: Direction, tiles: int
) -> Generator[tuple[int, int], None, None]:
    """Generate a simple path in the given direction from the origin."""
    origin_vec = Vector2(origin)
    for _ in range(tiles):
        origin_vec += dirs2[direction]
        yield (int(origin_vec.x), int(origin_vec.y))


def parse_path_parameters(
    origin: tuple[int, int], move_list: Sequence[str]
) -> Generator[tuple[int, int], None, None]:
    """Parse a list of move commands and generate the corresponding path."""
    for move in move_list:
        move = move.strip()
        if not move:
            continue

        parts = move.split(maxsplit=1)
        direction = parts[0].lower()
        tiles_str = parts[1] if len(parts) > 1 else "1"

        try:
            direction_enum = Direction(direction)
        except ValueError:
            raise ValueError(f"Invalid direction '{direction}'")

        try:
            tiles = int(tiles_str)
            if tiles <= 0:
                continue
        except ValueError:
            raise ValueError(f"Invalid tile count '{tiles_str}'")

        for point in simple_path(origin, direction_enum, tiles):
            yield point
        origin = point


def get_coords(
    tile: tuple[int, int], map_size: tuple[int, int], radius: int = 1
) -> list[tuple[int, int]]:
    """
    Returns a list with the cardinal coordinates (down, right, up, and left),
    Negative coordinates as well as the ones that exceed the map size will be
    filtered out. If no valid coordinates are found (i.e., the radius is too large
    to fit within the map), then a ValueError will be raised. If the radius is 0,
    the function will return a list containing the original tile.

     -  | 1,0 |  -
    0,1 |     | 2,1 |
     -  | 1,2 |  -

    eg. origin (1,1), radius = 1 = (1,0),(0,1),(1,2),(2,1)

    Parameters:
        tile: Tile coordinates
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        List tile coordinates.
    """
    x, y = tile
    width, height = map_size
    if radius < 0:
        raise ValueError(f"Radius cannot be negative: {radius}")

    if radius == 0:
        return [(x, y)]

    coords = [
        (x, y + radius),  # down
        (x + radius, y),  # right
        (x, y - radius),  # up
        (x - radius, y),  # left
    ]

    valid_coords = [
        coord
        for coord in coords
        if 0 <= coord[0] < width and 0 <= coord[1] < height
    ]

    if not valid_coords:
        raise ValueError(
            f"No valid coordinates found for tile {tile} with radius {radius} in map {map_size}"
        )

    return valid_coords


def get_coord_direction(
    tile: tuple[int, int],
    direction: Direction,
    map_size: tuple[int, int],
    radius: int = 1,
) -> tuple[int, int]:
    """
    Returns the coordinates for a specific direction and radius.
    Negative coordinates as well as the ones that exceed the map size will
    raise a ValueError.

    Parameters:
        tile: Tile coordinates
        direction: Direction "up*, "dowm", "left", "right"
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        Tuple tile coordinates.
    """
    if radius < 0:
        raise ValueError(f"Radius cannot be negative: {radius}")

    if radius == 0:
        return tile

    dx, dy = dirs2[direction]
    new_tile = (
        tile[0] + int(dx) * radius,
        tile[1] + int(dy) * radius,
    )

    if 0 <= new_tile[0] < map_size[0] and 0 <= new_tile[1] < map_size[1]:
        return new_tile
    else:
        raise ValueError(
            f"{new_tile} are invalid coordinates within map {map_size}"
        )


def get_adjacent_position(
    position: tuple[int, int],
    direction: Direction,
) -> tuple[int, int]:
    """
    Returns the adjacent position in the given direction.

    Parameters:
        position: The original position.
        direction: The direction to move.

    Returns:
        The adjacent position.
    """
    dx, dy = dirs2[direction]
    x, y = position
    return (x + int(dx), y + int(dy))


def get_direction(
    base: Union[Vector2, tuple[int, int]],
    target: Union[Vector2, tuple[int, int]],
) -> Direction:
    """
    Return the direction based on the coordinates position.

    eg. base (1,3) - target (1,12) -> "down"

    Parameters:
        base: Base coordinates
        target: Target coordinates

    Returns:
        Direction.
    """
    y_offset = base[1] - target[1]
    x_offset = base[0] - target[0]
    # Is it further away vertically or horizontally?
    look_on_y_axis = abs(y_offset) >= abs(x_offset)

    if look_on_y_axis:
        return Direction.up if y_offset > 0 else Direction.down
    else:
        return Direction.left if x_offset > 0 else Direction.right


def pairs(direction: Direction) -> Direction:
    """
    Returns complimentary direction.

    Parameters:
        direction: Direction.

    Returns:
        Complimentary direction.
    """
    opposites = {
        Direction.up: Direction.down,
        Direction.down: Direction.up,
        Direction.left: Direction.right,
        Direction.right: Direction.left,
    }
    opposite = opposites.get(direction)
    if opposite is None:
        raise ValueError(f"{direction} doesn't exist.")
    return opposite


def proj(point: Vector3) -> Vector2:
    """
    Project 3d coordinates to 2d.

    Not necessarily for use on a screen.

    Parameters:
        point: The 3d vector to project.

    Returns:
        2d projection vector.
    """
    return Vector2(point.x, point.y)


def tiles_inside_rect(
    rect: ReadOnlyRect,
    grid_size: tuple[int, int],
) -> Generator[tuple[int, int], None, None]:
    """
    Iterate all tile positions within this rect.

    The positions will be changed from pixel/map coords to tile coords.

    Parameters:
        rect: Area to get tiles in.
        grid_size: Size of each tile.

    Yields:
        Tile positions inside the rect.
    """
    # scan order is left->right, top->bottom
    for y, x in product(
        range(rect.top, rect.bottom, grid_size[1]),
        range(rect.left, rect.right, grid_size[0]),
    ):
        yield x // grid_size[0], y // grid_size[1]


def snap_interval(value: float, interval: int) -> int:
    value = round_to_divisible(value)
    if value == interval:
        return value - 1
    return value


def snap_outer_point(
    point: tuple[int, int],
    grid_size: tuple[int, int],
) -> tuple[int, int]:
    """
    Snap point to nearest grid intersection.

    * If point is rounded up, the coords are 1 less on each axis.

    Parameters:
        point: Point to snap.
        grid_size: Grid size.

    Returns:
        Snapped point.
    """
    return (
        snap_interval(point[0], grid_size[0]),
        snap_interval(point[1], grid_size[1]),
    )


def snap_point(
    point: tuple[int, int],
    grid_size: tuple[int, int],
) -> tuple[int, int]:
    """
    Snap point to nearest grid intersection.

    Parameters:
        point: Point to snap.
        grid_size: Grid size.

    Returns:
        Snapped point.
    """
    return (
        round_to_divisible(point[0], grid_size[0]),
        round_to_divisible(point[1], grid_size[1]),
    )


def point_to_grid(
    point: tuple[int, int],
    grid_size: tuple[int, int],
) -> tuple[int, int]:
    """
    Snap pixel coordinate to grid, then convert to tile coords.

    Parameters:
        point: Point to snap.
        grid_size: Grid size.

    Returns:
        Snapped point.
    """
    point = snap_point(point, grid_size)
    return point[0] // grid_size[0], point[1] // grid_size[1]


def angle_of_points(
    point0: tuple[int, int],
    point1: tuple[int, int],
) -> float:
    """
    Find angle between two points.

    Parameters:
        point0: First point.
        point1: Second point.

    Returns:
        Angle between the two points.
    """
    ang = atan2(-(point1[1] - point0[1]), point1[0] - point0[0])
    if ang < 0:
        ang += 2 * pi
    return ang


def snap_rect(
    rect: RectTypeVar,
    grid_size: tuple[int, int],
) -> RectTypeVar:
    """
    Align all vertices to the nearest point.

    Parameters:
        rect: Rect to snap.
        grid_size: Grid size.

    Returns:
        Snapped rect.
    """
    left, top = snap_point(rect.topleft, grid_size)
    right, bottom = snap_point(rect.bottomright, grid_size)
    return type(rect)((left, top, right - left, bottom - top))


def orientation_by_angle(angle: float) -> Orientation:
    """Return "horizontal" or "vertical".

    Parameters:
        angle: Angle with the horizontal axis.

    Returns:
        Whether the orientation is horizontal or vertical.
    """
    if angle in {0.0, 2 * pi}:
        return Orientation.horizontal
    elif angle in {pi / 2, 3 * pi / 2}:
        return Orientation.vertical
    else:
        raise ValueError("A collision line must be aligned to an axis")


def get_coords_ext(
    tile: tuple[int, int], map_size: tuple[int, int], radius: int = 1
) -> list[tuple[int, int]]:
    """
    Returns a list with all the coordinates (down, right, up, left, upper left,
    upper right, bottom left, bottom right).
    Negative coordinates as well as the ones that exceed the map size will be
    filtered out. If no valid coordinates, then it'll be raised a ValueError.

    0,0 | 1,0 | 2,0 |
    0,1 |     | 2,1 |
    0,2 | 1,2 | 2,2 |

    eg. origin (1,1), radius = 1 = (0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2)

    Parameters:
        tile: Tile coordinates
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        List tile coordinates.
    """
    if radius < 0:
        raise ValueError(f"Radius cannot be negative: {radius}")

    x, y = tile
    width, height = map_size

    coords = {
        (x + dx, y + dy)
        for dx in range(-radius, radius + 1)
        for dy in range(-radius, radius + 1)
        if (dx, dy) != (0, 0) and 0 <= x + dx < width and 0 <= y + dy < height
    }

    if not coords:
        raise ValueError(
            f"No valid coordinates found for tile {tile} with radius {radius} in map {map_size}"
        )

    return list(coords)


def get_explicit_tile_exits(
    position: tuple[int, int],
    tile: RegionProperties,
    facing: Direction,
    skip_nodes: Optional[set[tuple[int, int]]] = None,
) -> list[tuple[float, ...]]:
    """
    Check for exits from tile which are defined in the map.

    This will return exits which were defined by the map creator.

    Checks "endure" and "exits" properties of the tile.

    Parameters:
        position: Original position.
        tile: Region properties of the tile.
        facing: Character facing.
        skip_nodes: Set of nodes to skip.
    """
    skip_nodes = skip_nodes or set()
    exits: list[tuple[float, ...]] = []

    try:
        # Check if the player's current position has any exit limitations.
        if tile.endure:
            direction = (
                facing
                if len(tile.endure) > 1 or not tile.endure
                else tile.endure[0]
            )
            exit_position = tuple(dirs2[direction] + position)
            if exit_position not in skip_nodes:
                exits.append(exit_position)

        # Check if the tile explicitly defines exits.
        if tile.exit_from:
            exits.extend(
                tuple(dirs2[direction] + position)
                for direction in tile.exit_from
                if tuple(dirs2[direction] + position) not in skip_nodes
            )
    except (KeyError, TypeError):
        return []
    return exits


def get_pos_from_tilepos(
    current_map: AbstractMap, tile_position: Vector2
) -> tuple[int, int]:
    """
    Returns the map pixel coordinates based on the tile position.

    This method calculates the pixel coordinates on the map corresponding
    to the specified tile position, accounting for the map's center offset.
    Use this method for drawing elements on the screen.

    Parameters:
        current_map: The map object (`AbstractMap`) containing the renderer
            and relevant positional data.
        tile_position: A [x, y] tile position represented as a `Vector2`.

    Returns:
        A tuple representing the pixel coordinates (x, y) to draw at the
        given tile position, adjusted for the map's center offset.
    """
    assert current_map.renderer
    cx, cy = current_map.renderer.get_center_offset()
    px, py = project(tile_position)
    x = px + cx
    y = py + cy
    return x, y
