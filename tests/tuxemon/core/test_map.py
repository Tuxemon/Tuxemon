import unittest

from tuxemon.compat import Rect
from tuxemon.core.map import snap_interval, snap_point, snap_rect, tiles_inside_rect, point_to_grid


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
