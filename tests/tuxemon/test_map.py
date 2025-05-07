# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from math import pi
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.compat import Rect
from tuxemon.db import Direction, Orientation
from tuxemon.map import (
    angle_of_points,
    direction_to_list,
    get_adjacent_position,
    get_coord_direction,
    get_coords,
    get_coords_ext,
    get_direction,
    get_explicit_tile_exits,
    get_pos_from_tilepos,
    orientation_by_angle,
    pairs,
    point_to_grid,
    snap_interval,
    snap_point,
    snap_rect,
    tiles_inside_rect,
)
from tuxemon.math import Vector2


class TestSnapInterval(unittest.TestCase):
    def test_round_up(self):
        value = 14
        interval = 16
        expected = 15
        result = snap_interval(value, interval)
        self.assertEqual(expected, result)

    def test_round_down(self):
        value = 1
        interval = 16
        expected = 0
        result = snap_interval(value, interval)
        self.assertEqual(expected, result)

    def test_result_is_int(self):
        result = snap_interval(0, 16)
        self.assertIsInstance(result, int)


class TestSnapPoint(unittest.TestCase):
    def test_round_up(self):
        point = (14, 15)
        grid_size = (16, 16)
        expected = (16, 16)
        result = snap_point(point, grid_size)
        self.assertEqual(expected, result)

    def test_round_down(self):
        point = (1, 2)
        grid_size = (16, 16)
        expected = (0, 0)
        result = snap_point(point, grid_size)
        self.assertEqual(expected, result)

    def test_result_is_tuple(self):
        point = (9, 9)
        grid_size = (16, 16)
        result = snap_point(point, grid_size)
        self.assertIsInstance(result, tuple)

    def test_result_is_int(self):
        point = (9, 9)
        grid_size = (16, 16)
        result = snap_point(point, grid_size)
        self.assertTrue(all(isinstance(i, int) for i in result))


class TestPointToGrid(unittest.TestCase):
    def test_round_up(self):
        point = (32, 44)
        grid_size = (16, 16)
        expected = (2, 3)
        result = point_to_grid(point, grid_size)
        self.assertEqual(expected, result)

    def test_round_down(self):
        point = (32, 50)
        grid_size = (16, 16)
        expected = (2, 3)
        result = point_to_grid(point, grid_size)
        self.assertEqual(expected, result)

    def test_result_is_tuple(self):
        point = (32, 32)
        grid_size = (16, 16)
        result = point_to_grid(point, grid_size)
        self.assertIsInstance(result, tuple)

    def test_result_is_int(self):
        point = (32, 32)
        grid_size = (16, 16)
        result = point_to_grid(point, grid_size)
        self.assertTrue(all(isinstance(i, int) for i in result))


class TestSnapRect(unittest.TestCase):
    def test_snap_rect_result_is_rect(self):
        rect = Rect(1, 1, 14, 14)
        grid_size = (16, 16)
        result = snap_rect(rect, grid_size)
        self.assertIsInstance(result, Rect)

    def test_snap_x_axis(self):
        rect = Rect(1, 16, 30, 16)
        grid_size = (16, 16)
        result = snap_rect(rect, grid_size)
        self.assertEqual(0, result.x)
        self.assertEqual(16, result.y)
        self.assertEqual(32, result.w)
        self.assertEqual(16, result.h)

    def test_snap_y_axis(self):
        rect = Rect(1, 16, 16, 30)
        grid_size = (16, 16)
        result = snap_rect(rect, grid_size)
        self.assertEqual(0, result.x)
        self.assertEqual(16, result.y)
        self.assertEqual(16, result.w)
        self.assertEqual(32, result.h)


class TestTilesInsideRect(unittest.TestCase):
    def test_correct_result(self):
        rect = Rect(0, 16, 32, 48)
        grid_size = (16, 16)
        expected = [(0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3)]
        result = list(tiles_inside_rect(rect, grid_size))
        self.assertEqual(expected, result)

    def test_invalid_grid_size(self):
        rect = Rect(0, 0, 10, 10)
        grid_size = (0, 2)
        with self.assertRaises(ValueError):
            list(tiles_inside_rect(rect, grid_size))

    def test_rect_with_no_tiles(self):
        rect = Rect(0, 0, 1, 1)
        grid_size = (2, 2)
        self.assertEqual(list(tiles_inside_rect(rect, grid_size)), [(0, 0)])


class TestAngleOfPoints(unittest.TestCase):
    def test_horizontal_right(self):
        self.assertEqual(angle_of_points((0, 0), (1, 0)), 0.0)

    def test_horizontal_left(self):
        self.assertTrue(angle_of_points((0, 0), (-1, 0)), pi)

    def test_vertical_up(self):
        self.assertTrue(angle_of_points((0, 0), (0, 1)), pi / 2)

    def test_vertical_down(self):
        self.assertTrue(angle_of_points((0, 0), (0, -1)), 3 * pi / 2)

    def test_diagonal(self):
        self.assertTrue(angle_of_points((0, 0), (1, 1)), pi / 4)

    def test_arbitrary_angle(self):
        result = angle_of_points((2, 3), (5, 7))
        expected = 0.9272952180016122
        self.assertTrue(result, expected)


class TestOrientationByAngle(unittest.TestCase):
    def test_vertical(self):
        angle = 3 / 2 * pi
        self.assertEqual(orientation_by_angle(angle), Orientation.vertical)

    def test_horizontal(self):
        angle = 0.0
        self.assertEqual(orientation_by_angle(angle), Orientation.horizontal)

    def test_not_aligned(self):
        angle = pi / 4
        with self.assertRaises(Exception):
            orientation_by_angle(angle)

    def test_vertical_with_tolerance(self):
        angle = 3 / 2 * pi + 1e-7
        with self.assertRaises(Exception):
            orientation_by_angle(angle)

    def test_horizontal_with_tolerance(self):
        angle = 1e-7
        with self.assertRaises(Exception):
            orientation_by_angle(angle)

    def test_near_two_pi(self):
        angle = 2 * pi - 1e-7
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_negative_angle(self):
        angle = -pi / 2
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_exact_pi(self):
        angle = pi
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_random_non_aligned(self):
        angle = pi / 3  # 60 degrees
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_extreme_values_positive(self):
        angle = 10 * pi
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_extreme_values_negative(self):
        angle = -5 * pi
        with self.assertRaises(ValueError):
            orientation_by_angle(angle)

    def test_large_input_set(self):
        angles = [0.0, pi / 2, pi, 3 * pi / 2, 2 * pi] * 1000
        for angle in angles:
            if angle in {0.0, 2 * pi}:
                self.assertEqual(
                    orientation_by_angle(angle), Orientation.horizontal
                )
            elif angle in {pi / 2, 3 * pi / 2}:
                self.assertEqual(
                    orientation_by_angle(angle), Orientation.vertical
                )
            else:
                with self.assertRaises(ValueError):
                    orientation_by_angle(angle)


class TestGetCoordsExt(unittest.TestCase):
    def test_valid_coordinates(self):
        tile = (1, 1)
        map_size = (3, 3)
        radius = 1
        self.assertEqual(len(get_coords_ext(tile, map_size, radius)), 8)

    def test_negative_coordinates(self):
        tile = (0, 0)
        map_size = (3, 3)
        radius = 1
        expected_coords = [(0, 1), (1, 0), (1, 1)]
        self.assertEqual(
            get_coords_ext(tile, map_size, radius), expected_coords
        )

    def test_out_of_bounds_coordinates(self):
        tile = (2, 2)
        map_size = (3, 3)
        radius = 1
        expected_coords = [(1, 1), (1, 2), (2, 1)]
        self.assertEqual(
            get_coords_ext(tile, map_size, radius), expected_coords
        )

    def test_no_valid_coordinates(self):
        tile = (0, 0)
        map_size = (0, 0)
        radius = 1
        with self.assertRaises(ValueError):
            get_coords_ext(tile, map_size, radius)

    def test_radius_zero(self):
        tile = (1, 1)
        map_size = (3, 3)
        radius = 0
        with self.assertRaises(ValueError):
            get_coords_ext(tile, map_size, radius)

    def test_larger_radius(self):
        tile = (1, 1)
        map_size = (5, 5)
        radius = 2
        self.assertEqual(len(get_coords_ext(tile, map_size, radius)), 15)

    def test_map_size_one(self):
        tile = (0, 0)
        map_size = (1, 1)
        radius = 1
        with self.assertRaises(ValueError):
            get_coords_ext(tile, map_size, radius)

    def test_radius_larger_than_map(self):
        tile = (1, 1)
        map_size = (3, 3)
        radius = 3
        self.assertEqual(len(get_coords_ext(tile, map_size, radius)), 8)

    def test_tile_on_map_edge(self):
        tile = (0, 0)
        map_size = (3, 3)
        radius = 1
        expected_coords = [(0, 1), (1, 0), (1, 1)]
        self.assertEqual(
            get_coords_ext(tile, map_size, radius), expected_coords
        )

    def test_diagonal_corner(self):
        tile = (0, 0)
        map_size = (2, 2)
        radius = 1
        expected_coords = [(0, 1), (1, 0), (1, 1)]
        self.assertEqual(
            get_coords_ext(tile, map_size, radius),
            expected_coords,
        )

    def test_different_radius(self):
        tile = (2, 2)
        map_size = (5, 5)
        radius = 2
        self.assertEqual(len(get_coords_ext(tile, map_size, radius)), 24)


class TestGetCoords(unittest.TestCase):
    def test_valid_coordinates(self):
        map_size = (5, 5)
        tile = (2, 2)
        radius = 1
        expected_coords = [(2, 3), (3, 2), (2, 1), (1, 2)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_radius_greater_than_one(self):
        map_size = (5, 5)
        tile = (2, 2)
        radius = 2
        expected_coords = [(2, 4), (4, 2), (2, 0), (0, 2)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_tile_at_edge(self):
        map_size = (5, 5)
        tile = (0, 0)
        radius = 1
        expected_coords = [(0, 1), (1, 0)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_tile_out_of_bounds(self):
        map_size = (5, 5)
        tile = (6, 6)
        radius = 1
        with self.assertRaises(ValueError):
            get_coords(tile, map_size, radius)

    def test_no_valid_coordinates(self):
        map_size = (1, 1)
        tile = (0, 0)
        radius = 2
        with self.assertRaises(ValueError):
            get_coords(tile, map_size, radius)

    def test_large_map_and_radius(self):
        map_size = (100, 100)
        tile = (50, 50)
        radius = 10
        expected_coords = [(50, 60), (60, 50), (50, 40), (40, 50)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_negative_radius(self):
        map_size = (5, 5)
        tile = (2, 2)
        radius = -1

        with self.assertRaises(ValueError):
            get_coords(tile, map_size, radius)

    def test_zero_radius(self):
        map_size = (5, 5)
        tile = (2, 2)
        radius = 0
        expected_coords = [(2, 2)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_tile_on_map_edge_with_large_radius(self):
        map_size = (10, 10)
        tile = (0, 0)
        radius = 5
        expected_coords = [(0, 5), (5, 0)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)

    def test_tile_in_corner_with_large_radius(self):
        map_size = (10, 10)
        tile = (0, 0)
        radius = 7
        expected_coords = [(0, 7), (7, 0)]
        self.assertEqual(get_coords(tile, map_size, radius), expected_coords)


class TestGetCoordDirection(unittest.TestCase):
    def test_valid_coordinates(self):
        map_size = (10, 10)
        tile = (5, 5)
        radius = 1

        # Test all directions
        self.assertEqual(
            get_coord_direction(tile, Direction.up, map_size, radius), (5, 4)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.down, map_size, radius), (5, 6)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.left, map_size, radius), (4, 5)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.right, map_size, radius),
            (6, 5),
        )

    def test_out_of_bounds_coordinates(self):
        map_size = (5, 5)
        tile = (0, 0)
        radius = 1

        with self.assertRaises(ValueError):
            get_coord_direction(tile, Direction.up, map_size, radius)
        with self.assertRaises(ValueError):
            get_coord_direction(tile, Direction.left, map_size, radius)

    def test_negative_coordinates(self):
        map_size = (5, 5)
        tile = (4, 4)
        radius = 2

        self.assertEqual(
            get_coord_direction(tile, Direction.left, map_size, radius),
            (2, 4),
        )

    def test_valid_coordinates_edge_cases(self):
        map_size = (10, 10)
        radius = 1

        self.assertEqual(
            get_coord_direction((0, 0), Direction.down, map_size, radius),
            (0, 1),
        )
        self.assertEqual(
            get_coord_direction((9, 9), Direction.up, map_size, radius), (9, 8)
        )
        self.assertEqual(
            get_coord_direction((0, 5), Direction.right, map_size, radius),
            (1, 5),
        )
        self.assertEqual(
            get_coord_direction((5, 9), Direction.left, map_size, radius),
            (4, 9),
        )

    def test_different_radii(self):
        map_size = (10, 10)
        tile = (5, 5)

        # Test different radii
        self.assertEqual(
            get_coord_direction(tile, Direction.up, map_size, 2), (5, 3)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.down, map_size, 0), (5, 5)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.left, map_size, 3), (2, 5)
        )

    def test_large_map(self):
        map_size = (100, 100)
        tile = (50, 50)
        radius = 10

        # Test with a large map and radius
        self.assertEqual(
            get_coord_direction(tile, Direction.up, map_size, radius), (50, 40)
        )
        self.assertEqual(
            get_coord_direction(tile, Direction.right, map_size, radius),
            (60, 50),
        )

    def test_invalid_map_size(self):
        tile = (5, 5)
        radius = 1

        # Test invalid map sizes
        with self.assertRaises(ValueError):
            get_coord_direction(tile, Direction.up, (0, 0), radius)
        with self.assertRaises(ValueError):
            get_coord_direction(tile, Direction.down, (-1, 5), radius)


class TestGetAdjacentPosition(unittest.TestCase):
    def test_get_adjacent_position_up(self):
        position = (0, 0)
        direction = Direction.up
        expected_neighbor = (0, -1)
        self.assertEqual(
            get_adjacent_position(position, direction), expected_neighbor
        )

    def test_get_adjacent_position_down(self):
        position = (0, 0)
        direction = Direction.down
        expected_neighbor = (0, 1)
        self.assertEqual(
            get_adjacent_position(position, direction), expected_neighbor
        )

    def test_get_adjacent_position_left(self):
        position = (0, 0)
        direction = Direction.left
        expected_neighbor = (-1, 0)
        self.assertEqual(
            get_adjacent_position(position, direction), expected_neighbor
        )

    def test_get_adjacent_position_right(self):
        position = (0, 0)
        direction = Direction.right
        expected_neighbor = (1, 0)
        self.assertEqual(
            get_adjacent_position(position, direction), expected_neighbor
        )

    def test_get_adjacent_position_invalid_direction(self):
        position = (0, 0)
        direction = "InvalidDirection"
        with self.assertRaises(KeyError):
            get_adjacent_position(position, direction)

    def test_get_adjacent_position_invalid_position(self):
        position = "InvalidPosition"
        direction = Direction.up
        with self.assertRaises(ValueError):
            get_adjacent_position(position, direction)


class TestGetDirection(unittest.TestCase):
    def test_up(self):
        self.assertEqual(get_direction((1, 3), (1, 1)), Direction.up)

    def test_down(self):
        self.assertEqual(get_direction((1, 1), (1, 3)), Direction.down)

    def test_left(self):
        self.assertEqual(get_direction((3, 1), (1, 1)), Direction.left)

    def test_right(self):
        self.assertEqual(get_direction((1, 1), (3, 1)), Direction.right)

    def test_diagonal_up_right(self):
        self.assertEqual(get_direction((1, 1), (3, 3)), Direction.down)

    def test_diagonal_down_left(self):
        self.assertEqual(get_direction((3, 3), (1, 1)), Direction.up)

    def test_large_offsets(self):
        self.assertEqual(
            get_direction((1000, 1000), (1001, 1000)), Direction.right
        )
        self.assertEqual(
            get_direction((1000, 1000), (999, 1000)), Direction.left
        )
        self.assertEqual(
            get_direction((1000, 1000), (1000, 1001)), Direction.down
        )
        self.assertEqual(
            get_direction((1000, 1000), (1000, 999)), Direction.up
        )

    def test_negative_coordinates(self):
        self.assertEqual(get_direction((-1, -1), (-2, -1)), Direction.left)
        self.assertEqual(get_direction((-1, -1), (0, -1)), Direction.right)
        self.assertEqual(get_direction((-1, -1), (-1, 0)), Direction.down)
        self.assertEqual(get_direction((-1, -1), (-1, -2)), Direction.up)

    def test_zero_offset(self):
        self.assertEqual(get_direction((1, 2), (1, 2)), Direction.down)
        self.assertEqual(get_direction((2, 1), (2, 3)), Direction.down)
        self.assertEqual(get_direction((3, 1), (1, 1)), Direction.left)
        self.assertEqual(get_direction((1, 1), (3, 1)), Direction.right)

    def test_edge_cases(self):
        self.assertEqual(get_direction((1, 2), (2, 3)), Direction.down)
        self.assertEqual(get_direction((2, 3), (1, 2)), Direction.up)
        self.assertEqual(get_direction((2, 1), (4, 2)), Direction.right)
        self.assertEqual(get_direction((4, 2), (2, 1)), Direction.left)


class TestPairsFunction(unittest.TestCase):
    def test_up_down(self):
        self.assertEqual(pairs(Direction.up), Direction.down)

    def test_down_up(self):
        self.assertEqual(pairs(Direction.down), Direction.up)

    def test_left_right(self):
        self.assertEqual(pairs(Direction.left), Direction.right)

    def test_right_left(self):
        self.assertEqual(pairs(Direction.right), Direction.left)

    def test_invalid_direction(self):
        with self.assertRaises(ValueError):
            pairs("invalid_direction")

    def test_none_direction(self):
        with self.assertRaises(ValueError):
            pairs(None)


class TestDirectionToList(unittest.TestCase):
    def test_empty_string_with_whitespace(self):
        with self.assertRaises(ValueError):
            direction_to_list("    ")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            direction_to_list("")

    def test_single_direction(self):
        result = direction_to_list("up")
        self.assertEqual(result, [Direction.up])

    def test_multiple_direction(self):
        result = direction_to_list("up,down,right")
        self.assertEqual(len(result), 3)

    def test_single_direction_with_whitespace(self):
        result = direction_to_list("   up    ")
        self.assertEqual(len(result), 1)

    def test_mutiple_direction_with_whitespace(self):
        result = direction_to_list("up   ,down  ,   right")
        self.assertEqual(len(result), 3)

    def test_repeated_directions(self):
        result = direction_to_list("up,up,down,down")
        self.assertEqual(len(result), 2)

    def test_insensitive_duplicates(self):
        result = direction_to_list("uP,dOWn")
        self.assertEqual(len(result), 2)

    def test_none_input(self):
        result = direction_to_list(None)
        self.assertEqual(result, [])

    def test_very_long_string(self):
        long_string = ",".join(["up"] * 100)
        result = direction_to_list(long_string)
        self.assertEqual(result, [Direction.up])

    def test_unicode_characters(self):
        with self.assertRaises(ValueError):
            direction_to_list("ä, ü, up")

    def test_invalid_direction(self):
        with self.assertRaises(ValueError):
            direction_to_list("invalid direction")


class TestGetExplicitTileExits(unittest.TestCase):

    def test_no_endure_no_exit_from(self):
        position = (1, 1)
        tile = MagicMock(endure=None, exit_from=[])
        facing = Direction.down
        skip_nodes = None

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        self.assertEqual(exits, [])

    def test_endure_with_no_skip_nodes(self):
        position = (1, 1)
        tile = MagicMock(endure=[Direction.down], exit_from=[])
        facing = Direction.down
        skip_nodes = None

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        self.assertEqual(exits, [(1, 2)])

    def test_endure_with_skip_nodes(self):
        position = (1, 1)
        tile = MagicMock(endure=[Direction.down], exit_from=[])
        facing = Direction.down
        skip_nodes = {(1, 2)}

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        self.assertEqual(exits, [])

    def test_exit_from_with_multiple_directions(self):
        position = (1, 1)
        tile = MagicMock(endure=None, exit_from=[Direction.up, Direction.left])
        facing = Direction.down
        skip_nodes = None

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        expected_exits = [(0, 1), (1, 0)]
        self.assertEqual(sorted(exits), sorted(expected_exits))

    def test_exit_from_with_skip_nodes(self):
        position = (1, 1)
        tile = MagicMock(endure=None, exit_from=[Direction.up, Direction.left])
        facing = Direction.down
        skip_nodes = {(1, 0)}

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        expected_exits = [(0, 1)]
        self.assertEqual(exits, expected_exits)

    def test_invalid_tile_properties(self):
        position = (1, 1)
        tile = MagicMock(side_effect=TypeError)
        facing = Direction.down
        skip_nodes = None

        exits = get_explicit_tile_exits(position, tile, facing, skip_nodes)
        self.assertEqual(exits, [])


class TestGetPosFromTilePos(unittest.TestCase):
    def test_get_pos_from_tilepos(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (50, 75)

        tile_position = Vector2(3, 4)

        expected_px = 3 * prepare.TILE_SIZE[0]
        expected_py = 4 * prepare.TILE_SIZE[1]
        expected_x = expected_px + 50
        expected_y = expected_py + 75
        expected_result = (expected_x, expected_y)

        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)

    def test_different_tile_size(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (50, 75)

        tile_position = Vector2(2, 3)

        expected_px = 2 * prepare.TILE_SIZE[0]
        expected_py = 3 * prepare.TILE_SIZE[1]
        expected_result = (expected_px + 50, expected_py + 75)

        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)

    def test_tile_position_origin(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (50, 75)

        tile_position = Vector2(0, 0)

        expected_result = (50, 75)
        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)

    def test_negative_tile_position(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (50, 75)

        tile_position = Vector2(-1, -2)

        expected_px = -1 * prepare.TILE_SIZE[0]
        expected_py = -2 * prepare.TILE_SIZE[1]
        expected_result = (expected_px + 50, expected_py + 75)

        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)

    def test_large_tile_position(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (50, 75)

        tile_position = Vector2(1000, 2000)

        expected_px = 1000 * prepare.TILE_SIZE[0]
        expected_py = 2000 * prepare.TILE_SIZE[1]
        expected_result = (expected_px + 50, expected_py + 75)

        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)

    def test_zero_center_offset(self):
        mock_map = MagicMock()
        mock_map.renderer.get_center_offset.return_value = (0, 0)

        tile_position = Vector2(5, 7)

        expected_px = 5 * prepare.TILE_SIZE[0]
        expected_py = 7 * prepare.TILE_SIZE[1]
        expected_result = (expected_px, expected_py)

        result = get_pos_from_tilepos(mock_map, tile_position)
        self.assertEqual(result, expected_result)
