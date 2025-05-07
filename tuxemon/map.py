# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from itertools import product
from math import atan2, pi
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, TypeVar, Union

import pyscroll
from pytmx import pytmx
from pytmx.pytmx import TiledMap

from tuxemon import prepare
from tuxemon.camera import project
from tuxemon.compat.rect import ReadOnlyRect
from tuxemon.db import Direction, Orientation
from tuxemon.event import EventObject
from tuxemon.graphics import scaled_image_loader
from tuxemon.locale import T
from tuxemon.math import Vector2, Vector3
from tuxemon.tools import round_to_divisible

if TYPE_CHECKING:
    from tuxemon.entity import Entity
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

RectTypeVar = TypeVar("RectTypeVar", bound=ReadOnlyRect)


class RegionProperties(NamedTuple):
    enter_from: Sequence[Direction]
    exit_from: Sequence[Direction]
    endure: Sequence[Direction]
    entity: Optional[Union[NPC, Entity[Any]]]
    key: Optional[str]


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


def extract_region_properties(
    properties: Mapping[str, Optional[str]],
) -> Optional[RegionProperties]:
    """
    Given a dictionary from Tiled properties, return a dictionary
    suitable for collision detection.

    The function expects the input dictionary to contain keys from the following set:
    {"enter_from", "exit_from", "endure", "key"}. The values for "enter_from", "exit_from",
    and "endure" should be strings representing directions, while the value for "key"
    should be a string representing a label.

    If the input dictionary contains an "exit_from" key but no "enter_from" key, the
    function will automatically calculate the "enter_from" directions based on the
    "exit_from" directions.

    If the input dictionary contains a "key" with the value "slide", the function will
    set all movement directions to all possible directions.

    Parameters:
        properties: A dictionary from Tiled properties.

    Returns:
        A dictionary suitable for collision detection.

    Raises:
        ValueError: If the input dictionary contains an invalid value.
    """
    if not properties:
        return None

    valid_keys = {"enter_from", "exit_from", "endure", "key"}
    if not any(key.lower() in valid_keys for key in properties):
        return None

    movements: dict[str, list[Direction]] = {
        "enter_from": [],
        "exit_from": [],
        "endure": [],
    }
    label = None

    for key, value in properties.items():
        key = key.lower()
        if key in ["enter_from", "exit_from", "endure"]:
            if value == "":
                raise ValueError(
                    f"Invalid value for '{key}': cannot be an empty string"
                )
            directions = direction_to_list(value)
            if directions is None:
                raise ValueError(f"Invalid directions for '{key}': {value}")
            movements[key] = directions
        elif key == "key":
            if value == "":
                raise ValueError(
                    f"Invalid value for 'key': cannot be an empty string"
                )
            label = value

    if movements["exit_from"] and not movements["enter_from"]:
        movements["enter_from"] = sorted(
            set(Direction) - set(movements["exit_from"]),
            key=lambda d: list(Direction).index(d),
        )

    if label == "slide":
        for key in movements:
            movements[key] = list(Direction)

    return RegionProperties(**movements, entity=None, key=label)


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


def direction_to_list(direction: Optional[str]) -> list[Direction]:
    """
    Splits direction string and returns a list with Direction/s

    Parameters:
        direction: str (eg. enter_from = "direction")

    Returns:
        List with Direction/s
    """
    if direction is None:
        return []
    return sorted(
        [
            Direction(d)
            for d in {d.strip().lower() for d in direction.split(",")}
        ]
    )


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
    current_map: TuxemonMap, tile_position: Vector2
) -> tuple[int, int]:
    """
    Returns the map pixel coordinates based on the tile position.

    This method calculates the pixel coordinates on the map corresponding
    to the specified tile position, accounting for the map's center offset.
    Use this method for drawing elements on the screen.

    Parameters:
        current_map: The map object (`TuxemonMap`) containing the renderer
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


class TuxemonMap:
    """
    Contains collisions geometry and events loaded from a file.

    Supports entity movement and pathfinding.
    """

    def __init__(
        self,
        events: Sequence[EventObject],
        inits: Sequence[EventObject],
        surface_map: MutableMapping[tuple[int, int], dict[str, float]],
        collision_map: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ],
        collisions_lines_map: set[tuple[tuple[int, int], Direction]],
        tiled_map: TiledMap,
        maps: dict[str, Any],
        filename: str,
    ) -> None:
        """Constructor

        Collision lines
        Player can walk in tiles, but cannot cross
        from one to another. Items in this list should be in the
        form of pairs, signifying that it is NOT possible to travel
        from the first tile to the second (but reverse may be
        possible, i.e. jumping). All pairs of tiles must be adjacent
        (not diagonal).

        Collision Lines Map
        Create a list of all pairs of adjacent tiles that are impassable (aka walls).
        example: ((5,4),(5,3), both)

        Parameters:
            events: List of map events.
            inits: List of events to be loaded once, when map is entered.
            surface_map: Surface map.
            collision_map: Collision map.
            collisions_lines_map: Collision map of lines.
            tiled_map: Original tiled map.
            maps: Dictionary of map properties.
            filename: Path of the map.
        """
        self.collision_map = collision_map
        self.surface_map = surface_map
        self.collision_lines_map = collisions_lines_map
        self.size = tiled_map.width, tiled_map.height
        self.area = tiled_map.width * tiled_map.height
        self.inits = inits
        self.events = events
        self.renderer: Optional[pyscroll.BufferedRenderer] = None
        self.edges = maps.get("edges")
        self.data = tiled_map
        self.sprite_layer = 2
        self.filename = filename
        self.maps = maps

        # optional fields
        self.slug = maps.get("slug", "")
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")
        # translated cardinal directions (signs)
        self.north_trans = self.set_cardinals("north", maps)
        self.south_trans = self.set_cardinals("south", maps)
        self.east_trans = self.set_cardinals("east", maps)
        self.west_trans = self.set_cardinals("west", maps)
        # inside (true), outside (none)
        self.inside = bool(maps.get("inside"))
        # scenario: spyder, xero or none
        _value = maps.get("scenario")
        self.scenario = None if _value is None else str(_value)
        # check type of location
        self.map_type = maps.get("map_type")

    def set_cardinals(self, cardinal: str, maps: dict[str, str]) -> str:
        cardinals = maps.get(cardinal, "-").split(",")
        if len(cardinals) == 1:
            return T.translate(cardinals[0])
        else:
            return " - ".join(T.translate(c) for c in cardinals)

    def initialize_renderer(self) -> None:
        """
        Initialize the renderer for the map and sprites.

        Returns:
            Renderer for the map.
        """
        visual_data = pyscroll.data.TiledMapData(self.data)
        # Behaviour at the edges.
        clamp = self.edges == "clamped"
        self.renderer = pyscroll.BufferedRenderer(
            visual_data,
            prepare.SCREEN_SIZE,
            clamp_camera=clamp,
            tall_sprites=2,
        )

    def reload_tiles(self) -> None:
        """Reload the map tiles."""
        if self.renderer is None:
            raise RuntimeError(
                "Renderer must be initialized before reloading tiles"
            )

        data = pytmx.TiledMap(
            self.data.filename,
            image_loader=scaled_image_loader,
            pixelalpha=True,
        )
        self.renderer.data.tmx.images = data.images
        self.renderer.redraw_tiles(self.renderer._buffer)
