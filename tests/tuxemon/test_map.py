# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from math import pi
from unittest.mock import MagicMock

import pytest

from tuxemon import prepare
from tuxemon.compat import Rect
from tuxemon.db import Direction, Orientation
from tuxemon.map.map import (
    angle_of_points,
    get_adjacent_position,
    get_coord_direction,
    get_coords,
    get_coords_ext,
    get_direction,
    get_explicit_tile_exits,
    get_pos_from_tilepos,
    orientation_by_angle,
    pairs,
    parse_path_parameters,
    point_to_grid,
    snap_interval,
    snap_point,
    snap_rect,
    tiles_inside_rect,
)
from tuxemon.math import Vector2


@pytest.mark.parametrize(
    "origin, moves, expected",
    [
        pytest.param((0, 0), ["up"], [(0, -1)], id="single-move"),
        pytest.param(
            (0, 0),
            ["up", "right", "down"],
            [(0, -1), (1, -1), (1, 0)],
            id="multiple-moves",
        ),
        pytest.param(
            (0, 0),
            ["up 2", "right 3"],
            [(0, -1), (0, -2), (1, -2), (2, -2), (3, -2)],
            id="moves-with-tiles",
        ),
        pytest.param((0, 0), [], [], id="empty-move-list"),
        pytest.param((0, 0), ["up  "], [(0, -1)], id="move-with-spaces"),
        pytest.param(
            (0, 0),
            ["up  ", " right 2  "],
            [(0, -1), (1, -1), (2, -1)],
            id="trailing-spaces",
        ),
        pytest.param((0, 0), ["left 1"], [(-1, 0)], id="boundary-left"),
        pytest.param(
            (0, 0),
            ["UP 2", "rIgHt 3"],
            [(0, -1), (0, -2), (1, -2), (2, -2), (3, -2)],
            id="case-insensitive",
        ),
        pytest.param((0, 0), ["up 0"], [], id="zero-movement"),
        pytest.param(
            (0, 0),
            ["right 10000"],
            [(i, 0) for i in range(1, 10001)],
            id="large-movement",
        ),
    ],
)
def test_parse_path_parameters_valid(origin, moves, expected):
    assert list(parse_path_parameters(origin, moves)) == expected


@pytest.mark.parametrize(
    "origin, moves",
    [
        pytest.param((0, 0), [" invalid"], id="invalid-direction"),
        pytest.param((0, 0), ["up abc"], id="invalid-tiles"),
        pytest.param(
            (0, 0), ["invalid", "wrong", "down 2"], id="multiple-invalid"
        ),
    ],
)
def test_parse_path_parameters_invalid(origin, moves):
    with pytest.raises(ValueError):
        list(parse_path_parameters(origin, moves))


@pytest.mark.parametrize(
    "value, interval, expected",
    [
        pytest.param(14, 16, 15, id="round-up"),
        pytest.param(1, 16, 0, id="round-down"),
    ],
)
def test_snap_interval_rounding(value, interval, expected):
    assert snap_interval(value, interval) == expected


def test_snap_interval_returns_int():
    result = snap_interval(0, 16)
    assert isinstance(result, int)


@pytest.mark.parametrize(
    "point, grid, expected",
    [
        pytest.param((14, 15), (16, 16), (16, 16), id="round-up"),
        pytest.param((1, 2), (16, 16), (0, 0), id="round-down"),
    ],
)
def test_snap_point_rounding(point, grid, expected):
    assert snap_point(point, grid) == expected


def test_snap_point_returns_tuple():
    result = snap_point((9, 9), (16, 16))
    assert isinstance(result, tuple)


def test_snap_point_elements_are_int():
    result = snap_point((9, 9), (16, 16))
    assert all(isinstance(i, int) for i in result)


@pytest.mark.parametrize(
    "point, grid, expected",
    [
        pytest.param((32, 44), (16, 16), (2, 3), id="round-up"),
        pytest.param((32, 50), (16, 16), (2, 3), id="round-down"),
    ],
)
def test_point_to_grid_rounding(point, grid, expected):
    assert point_to_grid(point, grid) == expected


def test_point_to_grid_returns_tuple():
    result = point_to_grid((32, 32), (16, 16))
    assert isinstance(result, tuple)


def test_point_to_grid_elements_are_int():
    result = point_to_grid((32, 32), (16, 16))
    assert all(isinstance(i, int) for i in result)


def test_snap_rect_returns_rect():
    rect = Rect(1, 1, 14, 14)
    result = snap_rect(rect, (16, 16))
    assert isinstance(result, Rect)


@pytest.mark.parametrize(
    "rect, grid, expected",
    [
        pytest.param(
            Rect(1, 16, 30, 16),
            (16, 16),
            (0, 16, 32, 16),
            id="snap-x-axis",
        ),
        pytest.param(
            Rect(1, 16, 16, 30),
            (16, 16),
            (0, 16, 16, 32),
            id="snap-y-axis",
        ),
    ],
)
def test_snap_rect_axes(rect, grid, expected):
    result = snap_rect(rect, grid)
    assert (result.x, result.y, result.w, result.h) == expected


@pytest.mark.parametrize(
    "rect, grid, expected",
    [
        pytest.param(
            Rect(0, 16, 32, 48),
            (16, 16),
            [(0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3)],
            id="correct-result",
        ),
        pytest.param(
            Rect(0, 0, 1, 1),
            (2, 2),
            [(0, 0)],
            id="rect-with-no-tiles",
        ),
    ],
)
def test_tiles_inside_rect_valid(rect, grid, expected):
    assert list(tiles_inside_rect(rect, grid)) == expected


@pytest.mark.parametrize(
    "rect, grid",
    [
        pytest.param(Rect(0, 0, 10, 10), (0, 2), id="invalid-grid-size"),
    ],
)
def test_tiles_inside_rect_invalid(rect, grid):
    with pytest.raises(ValueError):
        list(tiles_inside_rect(rect, grid))


@pytest.mark.parametrize(
    "p1, p2, expected",
    [
        pytest.param((0, 0), (1, 0), 0.0, id="horizontal-right"),
        pytest.param((0, 0), (-1, 0), pi, id="horizontal-left"),
        pytest.param((0, 0), (0, -1), pi / 2, id="vertical-up"),
        pytest.param((0, 0), (0, 1), 3 * pi / 2, id="vertical-down"),
        pytest.param((0, 0), (1, -1), pi / 4, id="diag-up-right"),
        pytest.param((0, 0), (1, 1), 7 * pi / 4, id="diag-down-right"),
        pytest.param(
            (2, 3),
            (5, 7),
            angle_of_points((2, 3), (5, 7)),
            id="arbitrary-angle",
        ),
    ],
)
def test_angle_of_points(p1, p2, expected):
    assert angle_of_points(p1, p2) == expected


@pytest.mark.parametrize(
    "angle, expected",
    [
        pytest.param(3 / 2 * pi, Orientation.VERTICAL, id="vertical"),
        pytest.param(0.0, Orientation.HORIZONTAL, id="horizontal"),
    ],
)
def test_orientation_by_angle_valid(angle, expected):
    assert orientation_by_angle(angle) == expected


@pytest.mark.parametrize(
    "angle, exc",
    [
        pytest.param(pi / 4, Exception, id="not-aligned"),
        pytest.param(3 / 2 * pi + 1e-7, Exception, id="vertical-tolerance"),
        pytest.param(1e-7, Exception, id="horizontal-tolerance"),
        pytest.param(2 * pi - 1e-7, ValueError, id="near-two-pi"),
        pytest.param(-pi / 2, ValueError, id="negative-angle"),
        pytest.param(pi, ValueError, id="exact-pi"),
        pytest.param(pi / 3, ValueError, id="random-non-aligned"),
        pytest.param(10 * pi, ValueError, id="extreme-positive"),
        pytest.param(-5 * pi, ValueError, id="extreme-negative"),
    ],
)
def test_orientation_by_angle_invalid(angle, exc):
    with pytest.raises(exc):
        orientation_by_angle(angle)


@pytest.mark.parametrize(
    "angle, expected",
    [
        pytest.param(0.0, Orientation.HORIZONTAL, id="0"),
        pytest.param(2 * pi, Orientation.HORIZONTAL, id="2pi"),
        pytest.param(pi / 2, Orientation.VERTICAL, id="pi2"),
        pytest.param(3 * pi / 2, Orientation.VERTICAL, id="3pi2"),
        pytest.param(pi, ValueError, id="pi-invalid"),
    ],
)
def test_orientation_by_angle_large_input_set(angle, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            orientation_by_angle(angle)
    else:
        assert orientation_by_angle(angle) == expected


@pytest.mark.parametrize(
    "tile, map_size, radius, expected",
    [
        pytest.param(
            (1, 1),
            (3, 3),
            1,
            8,
            id="valid-center-radius1",
        ),
        pytest.param(
            (0, 0),
            (3, 3),
            1,
            [(0, 1), (1, 0), (1, 1)],
            id="negative-coords-clamped",
        ),
        pytest.param(
            (2, 2),
            (3, 3),
            1,
            [(1, 1), (1, 2), (2, 1)],
            id="out-of-bounds-clamped",
        ),
        pytest.param(
            (1, 1),
            (5, 5),
            2,
            15,
            id="larger-radius",
        ),
        pytest.param(
            (1, 1),
            (3, 3),
            3,
            8,
            id="radius-larger-than-map",
        ),
        pytest.param(
            (0, 0),
            (3, 3),
            1,
            [(0, 1), (1, 0), (1, 1)],
            id="tile-on-edge",
        ),
        pytest.param(
            (0, 0),
            (2, 2),
            1,
            [(0, 1), (1, 0), (1, 1)],
            id="diagonal-corner",
        ),
        pytest.param(
            (2, 2),
            (5, 5),
            2,
            24,
            id="different-radius",
        ),
    ],
)
def test_get_coords_ext_valid(tile, map_size, radius, expected):
    result = get_coords_ext(tile, map_size, radius)
    if isinstance(expected, int):
        assert len(result) == expected
    else:
        assert result == expected


@pytest.mark.parametrize(
    "tile, map_size, radius",
    [
        pytest.param((0, 0), (0, 0), 1, id="no-valid-coords"),
        pytest.param((1, 1), (3, 3), 0, id="radius-zero"),
        pytest.param((0, 0), (1, 1), 1, id="map-size-one"),
    ],
)
def test_get_coords_ext_invalid(tile, map_size, radius):
    with pytest.raises(ValueError):
        get_coords_ext(tile, map_size, radius)


@pytest.mark.parametrize(
    "tile, map_size, radius, expected",
    [
        pytest.param(
            (2, 2),
            (5, 5),
            1,
            [(2, 3), (3, 2), (2, 1), (1, 2)],
            id="valid-radius1",
        ),
        pytest.param(
            (2, 2),
            (5, 5),
            2,
            [(2, 4), (4, 2), (2, 0), (0, 2)],
            id="radius-greater-than-one",
        ),
        pytest.param(
            (0, 0),
            (5, 5),
            1,
            [(0, 1), (1, 0)],
            id="tile-at-edge",
        ),
        pytest.param(
            (50, 50),
            (100, 100),
            10,
            [(50, 60), (60, 50), (50, 40), (40, 50)],
            id="large-map-and-radius",
        ),
        pytest.param(
            (2, 2),
            (5, 5),
            0,
            [(2, 2)],
            id="zero-radius",
        ),
        pytest.param(
            (0, 0),
            (10, 10),
            5,
            [(0, 5), (5, 0)],
            id="edge-large-radius",
        ),
        pytest.param(
            (0, 0),
            (10, 10),
            7,
            [(0, 7), (7, 0)],
            id="corner-large-radius",
        ),
    ],
)
def test_get_coords_valid(tile, map_size, radius, expected):
    assert get_coords(tile, map_size, radius) == expected


@pytest.mark.parametrize(
    "tile, map_size, radius",
    [
        pytest.param((6, 6), (5, 5), 1, id="tile-out-of-bounds"),
        pytest.param((0, 0), (1, 1), 2, id="no-valid-coordinates"),
        pytest.param((2, 2), (5, 5), -1, id="negative-radius"),
    ],
)
def test_get_coords_invalid(tile, map_size, radius):
    with pytest.raises(ValueError):
        get_coords(tile, map_size, radius)


@pytest.mark.parametrize(
    "tile, direction, map_size, radius, expected",
    [
        pytest.param((5, 5), Direction.UP, (10, 10), 1, (5, 4), id="up"),
        pytest.param((5, 5), Direction.DOWN, (10, 10), 1, (5, 6), id="down"),
        pytest.param((5, 5), Direction.LEFT, (10, 10), 1, (4, 5), id="left"),
        pytest.param((5, 5), Direction.RIGHT, (10, 10), 1, (6, 5), id="right"),
        pytest.param(
            (0, 0), Direction.DOWN, (10, 10), 1, (0, 1), id="edge-down"
        ),
        pytest.param((9, 9), Direction.UP, (10, 10), 1, (9, 8), id="edge-up"),
        pytest.param(
            (0, 5), Direction.RIGHT, (10, 10), 1, (1, 5), id="edge-right"
        ),
        pytest.param(
            (5, 9), Direction.LEFT, (10, 10), 1, (4, 9), id="edge-left"
        ),
        pytest.param(
            (5, 5), Direction.UP, (10, 10), 2, (5, 3), id="radius2-up"
        ),
        pytest.param(
            (5, 5), Direction.DOWN, (10, 10), 0, (5, 5), id="radius0-down"
        ),
        pytest.param(
            (5, 5), Direction.LEFT, (10, 10), 3, (2, 5), id="radius3-left"
        ),
        pytest.param(
            (50, 50), Direction.UP, (100, 100), 10, (50, 40), id="large-up"
        ),
        pytest.param(
            (50, 50),
            Direction.RIGHT,
            (100, 100),
            10,
            (60, 50),
            id="large-right",
        ),
    ],
)
def test_get_coord_direction_valid(
    tile, direction, map_size, radius, expected
):
    assert get_coord_direction(tile, direction, map_size, radius) == expected


@pytest.mark.parametrize(
    "tile, direction, map_size, radius",
    [
        pytest.param((0, 0), Direction.UP, (5, 5), 1, id="out-of-bounds-up"),
        pytest.param(
            (0, 0), Direction.LEFT, (5, 5), 1, id="out-of-bounds-left"
        ),
        pytest.param((5, 5), Direction.UP, (0, 0), 1, id="invalid-map-zero"),
        pytest.param(
            (5, 5), Direction.DOWN, (-1, 5), 1, id="invalid-map-negative"
        ),
    ],
)
def test_get_coord_direction_invalid(tile, direction, map_size, radius):
    with pytest.raises(ValueError):
        get_coord_direction(tile, direction, map_size, radius)


@pytest.mark.parametrize(
    "position, direction, expected",
    [
        pytest.param((0, 0), Direction.UP, (0, -1), id="up"),
        pytest.param((0, 0), Direction.DOWN, (0, 1), id="down"),
        pytest.param((0, 0), Direction.LEFT, (-1, 0), id="left"),
        pytest.param((0, 0), Direction.RIGHT, (1, 0), id="right"),
    ],
)
def test_get_adjacent_position_valid(position, direction, expected):
    assert get_adjacent_position(position, direction) == expected


@pytest.mark.parametrize(
    "position, direction, exc",
    [
        pytest.param(
            (0, 0), "InvalidDirection", KeyError, id="invalid-direction"
        ),
        pytest.param(
            "InvalidPosition", Direction.UP, ValueError, id="invalid-position"
        ),
    ],
)
def test_get_adjacent_position_invalid(position, direction, exc):
    with pytest.raises(exc):
        get_adjacent_position(position, direction)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param((1, 3), (1, 1), Direction.UP, id="up"),
        pytest.param((1, 1), (1, 3), Direction.DOWN, id="down"),
        pytest.param((3, 1), (1, 1), Direction.LEFT, id="left"),
        pytest.param((1, 1), (3, 1), Direction.RIGHT, id="right"),
        pytest.param((1, 1), (3, 3), Direction.DOWN, id="diag-up-right"),
        pytest.param((3, 3), (1, 1), Direction.UP, id="diag-down-left"),
        pytest.param(
            (1000, 1000), (1001, 1000), Direction.RIGHT, id="large-right"
        ),
        pytest.param(
            (1000, 1000), (999, 1000), Direction.LEFT, id="large-left"
        ),
        pytest.param(
            (1000, 1000), (1000, 1001), Direction.DOWN, id="large-down"
        ),
        pytest.param((1000, 1000), (1000, 999), Direction.UP, id="large-up"),
        pytest.param((-1, -1), (-2, -1), Direction.LEFT, id="neg-left"),
        pytest.param((-1, -1), (0, -1), Direction.RIGHT, id="neg-right"),
        pytest.param((-1, -1), (-1, 0), Direction.DOWN, id="neg-down"),
        pytest.param((-1, -1), (-1, -2), Direction.UP, id="neg-up"),
        pytest.param((1, 2), (1, 2), Direction.DOWN, id="zero-offset"),
        pytest.param((2, 1), (2, 3), Direction.DOWN, id="zero-offset-down"),
        pytest.param((3, 1), (1, 1), Direction.LEFT, id="zero-offset-left"),
        pytest.param((1, 1), (3, 1), Direction.RIGHT, id="zero-offset-right"),
        pytest.param((1, 2), (2, 3), Direction.DOWN, id="edge-down"),
        pytest.param((2, 3), (1, 2), Direction.UP, id="edge-up"),
        pytest.param((2, 1), (4, 2), Direction.RIGHT, id="edge-right"),
        pytest.param((4, 2), (2, 1), Direction.LEFT, id="edge-left"),
    ],
)
def test_get_direction(a, b, expected):
    assert get_direction(a, b) == expected


@pytest.mark.parametrize(
    "direction, expected",
    [
        pytest.param(Direction.UP, Direction.DOWN, id="up-down"),
        pytest.param(Direction.DOWN, Direction.UP, id="down-up"),
        pytest.param(Direction.LEFT, Direction.RIGHT, id="left-right"),
        pytest.param(Direction.RIGHT, Direction.LEFT, id="right-left"),
    ],
)
def test_pairs_valid(direction, expected):
    assert pairs(direction) == expected


@pytest.mark.parametrize(
    "direction",
    [
        pytest.param("invalid_direction", id="invalid-string"),
        pytest.param(None, id="none"),
    ],
)
def test_pairs_invalid(direction):
    with pytest.raises(ValueError):
        pairs(direction)


@pytest.mark.parametrize(
    "tile, facing, skip_nodes, expected",
    [
        pytest.param(
            MagicMock(endure=None, exit_from=[]),
            Direction.DOWN,
            None,
            [],
            id="no-endure-no-exit",
        ),
        pytest.param(
            MagicMock(endure=[Direction.DOWN], exit_from=[]),
            Direction.DOWN,
            None,
            [(1, 2)],
            id="endure-no-skip",
        ),
        pytest.param(
            MagicMock(endure=[Direction.DOWN], exit_from=[]),
            Direction.DOWN,
            {(1, 2)},
            [],
            id="endure-with-skip",
        ),
        pytest.param(
            MagicMock(endure=None, exit_from=[Direction.UP, Direction.LEFT]),
            Direction.DOWN,
            None,
            [(0, 1), (1, 0)],
            id="exit-from-multiple",
        ),
        pytest.param(
            MagicMock(endure=None, exit_from=[Direction.UP, Direction.LEFT]),
            Direction.DOWN,
            {(1, 0)},
            [(0, 1)],
            id="exit-from-with-skip",
        ),
    ],
)
def test_get_explicit_tile_exits(tile, facing, skip_nodes, expected):
    position = (1, 1)
    assert sorted(
        get_explicit_tile_exits(position, tile, facing, skip_nodes)
    ) == sorted(expected)


def test_get_explicit_tile_exits_invalid_tile():
    position = (1, 1)
    tile = MagicMock(side_effect=TypeError)
    facing = Direction.DOWN
    skip_nodes = None
    assert get_explicit_tile_exits(position, tile, facing, skip_nodes) == []


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.tile_size = prepare.DISPLAY_CONTEXT.tile_size
    return ctx


@pytest.mark.parametrize(
    "tilepos, offset",
    [
        pytest.param(Vector2(3, 4), (50, 75), id="basic"),
        pytest.param(Vector2(2, 3), (50, 75), id="different-size"),
        pytest.param(Vector2(0, 0), (50, 75), id="origin"),
        pytest.param(Vector2(-1, -2), (50, 75), id="negative"),
        pytest.param(Vector2(1000, 2000), (50, 75), id="large"),
        pytest.param(Vector2(5, 7), (0, 0), id="zero-offset"),
    ],
)
def test_get_pos_from_tilepos(tilepos, offset, context):
    mock_map = MagicMock()
    mock_map.renderer.get_center_offset.return_value = offset

    ts = context.tile_size
    expected_px = tilepos.x * ts[0]
    expected_py = tilepos.y * ts[1]
    expected = (expected_px + offset[0], expected_py + offset[1])

    assert get_pos_from_tilepos(mock_map, context, tilepos) == expected
