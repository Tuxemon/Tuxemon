# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    filtered out. If no valid coordinates, then it'll be raised a ValueError.

     -  | 1,0 |  -
    0,1 | 1,1 | 2,1 |
     -  | 1,2 |  -

    eg. radius = 1 (1,0),(0,1),(1,2),(2,1)

    Parameters:
        tile: Tile coordinates
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        List tile coordinates.
    """
    coords: list[tuple[int, int]] = []
    coords.append((tile[0], tile[1] + radius))  # down
    coords.append((tile[0] + radius, tile[1]))  # right
    coords.append((tile[0], tile[1] - radius))  # up
    coords.append((tile[0] - radius, tile[1]))  # left
    _coords = [
        _tile
        for _tile in coords
        if map_size[0] >= _tile[0] >= 0 and map_size[1] >= _tile[1] >= 0
    ]
    if not _coords:
        raise ValueError(f"{coords} invalid coordinates")
    return _coords


def get_coord_direction(
    tile: tuple[int, int],
    direction: Direction,
    map_size: tuple[int, int],
    radius: int = 1,
) -> tuple[int, int]:
    """
    Returns the coordinates for a specific side and radius.
    Negative coordinates as well as the ones that exceed the map size will
    raise a ValueError.

    Parameters:
        tile: Tile coordinates
        side: Direction "up*, "dowm", "left", "right"
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        Tuple tile coordinates.
    """
    _tile: tuple[int, int] = (0, 0)
    if direction == Direction.down:
        _tile = (tile[0], tile[1] + radius)
    elif direction == Direction.right:
        _tile = (tile[0] + radius, tile[1])
    elif direction == Direction.up:
        _tile = (tile[0], tile[1] - radius)
    elif direction == Direction.left:
        _tile = (tile[0] - radius, tile[1])
    else:
        raise ValueError(f"{direction} doesn't exist")
    if map_size[0] >= _tile[0] >= 0 and map_size[1] >= _tile[1] >= 0:
        return _tile
    else:
        raise ValueError(f"{_tile} invalid coordinates")


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
    if direction == Direction.up:
        return Direction.down
    elif direction == Direction.down:
        return Direction.up
    elif direction == Direction.left:
        return Direction.right
    elif direction == Direction.right:
        return Direction.left
    else:
        raise ValueError(f"{direction} doesn't exist.")


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
    ang = atan2(-(point1[1] - point0[1]), point1[0] - point1[0])
    ang %= 2 * pi
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
    if angle == 3 / 2 * pi:
        return Orientation.vertical
    elif angle == 0.0:
        return Orientation.horizontal
    else:
        raise Exception("A collision line must be aligned to an axis")


def extract_region_properties(
    properties: Mapping[str, str],
) -> Optional[RegionProperties]:
    """
    Given a dictionary from Tiled properties, return a dictionary
    suitable for collision detection.

    We are using word "endure" because continue is already used in Python
    and it can create issues. Endure means "continue to walk in a precise direction".

    If in the tileset.tsx there is endure=left, it means that the player continues
    walking left. endure is a sequence (possible multiple values); if there are more
    than 1 direction eg (up and left), then the player will continue in the direction
    he/she entered the tile, so it takes the direction from self.facing

    Uses `exit_from`, `enter_from`, and `continue` keys.

    Parameters:
        properties: Dictionary of data from Tiled for object, tile, etc.

    Returns:
        New dictionary for collision use.

    """
    # this could use a rewrite or re-thinking...
    label = None
    endure: list[Direction] = []
    enters: list[Direction] = []
    exits: list[Direction] = []
    has_movement_modifier = False
    for key in properties:
        if "enter_from" == key:
            enters = direction_to_list(properties[key])
            has_movement_modifier = True
        elif "exit_from" == key:
            exits = direction_to_list(properties[key])
            has_movement_modifier = True
        elif "endure" == key:
            endure = direction_to_list(properties[key])
            has_movement_modifier = True
        elif "key" == key:
            label = properties[key]
            has_movement_modifier = True
    # if there is an exit, but no explicit enter, then
    # allow entering from all sides except the exit side
    if exits and not enters:
        enters = list(Direction)
        for _exit in exits:
            enters.remove(_exit)
    if label == "slide":
        enters = list(Direction)
        exits = list(Direction)
        endure = list(Direction)
    if has_movement_modifier:
        return RegionProperties(
            enter_from=enters,
            exit_from=exits,
            endure=endure,
            entity=None,
            key=label,
        )
    else:
        return None


def get_coords_ext(
    tile: tuple[int, int], map_size: tuple[int, int], radius: int = 1
) -> list[tuple[int, int]]:
    """
    Returns a list with all the coordinates (down, right, up, left, upper left,
    upper right, bottom left, bottom right).
    Negative coordinates as well as the ones that exceed the map size will be
    filtered out. If no valid coordinates, then it'll be raised a ValueError.

    0,0 | 1,0 | 2,0 |
    0,1 | 1,1 | 2,1 |
    0,2 | 1,2 | 2,2 |

    eg. radius = 1
    (0,0),(1,0),(2,0),(0,1),(1,1),(2,1),(0,2),(1,2),(2,2)

    Parameters:
        tile: Tile coordinates
        map_size: Dimension of the map
        radius: Radius, default 1

    Returns:
        List tile coordinates.
    """
    coords: list[tuple[int, int]] = []
    coords.append((tile[0], tile[1] + radius))  # down
    coords.append((tile[0] + radius, tile[1]))  # right
    coords.append((tile[0], tile[1] - radius))  # up
    coords.append((tile[0] - radius, tile[1]))  # left
    coords.append((tile[0] - 1, tile[1] - 1))  # upper left
    coords.append((tile[0] + 1, tile[1] - 1))  # upper right
    coords.append((tile[0] - 1, tile[1] + 1))  # bottom left
    coords.append((tile[0] + 1, tile[1] + 1))  # bottom right
    _coords = [
        _tile
        for _tile in coords
        if map_size[0] >= _tile[0] >= 0 and map_size[1] >= _tile[1] >= 0
    ]
    if not _coords:
        raise ValueError(f"{coords} invalid coordinates")
    return _coords


def direction_to_list(direction: Optional[str]) -> list[Direction]:
    """
    Splits direction string and returns a list with Direction/s

    Parameters:
        direction: str (eg. enter_from = "direction")

    Returns:
        List with Direction/s

    """
    if direction is None:
        props = []
    else:
        props = direction.split(",")
    result: list[Direction] = []
    for _props in props:
        result.append(Direction(_props))
    return result


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


class TuxemonMap:
    """
    Contains collisions geometry and events loaded from a file.

    Supports entity movement and pathfinding.
    """

    def __init__(
        self,
        events: Sequence[EventObject],
        inits: Sequence[EventObject],
        surfable_map: Sequence[tuple[int, int]],
        collision_map: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ],
        collisions_lines_map: set[tuple[tuple[int, int], Direction]],
        tiled_map: TiledMap,
        maps: dict,
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
            surfable_map: Surfable map.
            collision_map: Collision map.
            collisions_lines_map: Collision map of lines.
            tiled_map: Original tiled map.
            maps: Dictionary of map properties.
            filename: Path of the map.

        """
        self.collision_map = collision_map
        self.surfable_map = surfable_map
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
        self.slug = str(maps.get("slug"))
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
        self.types = maps.get("types")

    def set_cardinals(self, cardinal: str, maps: dict[str, str]) -> str:
        cardinals = str(maps.get(cardinal, "-")).split(",")
        _cardinals = ""
        if len(cardinals) > 1:
            for _cardinal in cardinals:
                _cardinals += T.translate(_cardinal) + " - "
            return _cardinals[:-3]
        else:
            return T.translate(cardinals[0])

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
        data = pytmx.TiledMap(
            self.data.filename,
            image_loader=scaled_image_loader,
            pixelalpha=True,
        )
        assert self.renderer
        self.renderer.data.tmx.images = data.images
        self.renderer.redraw_tiles(self.renderer._buffer)
