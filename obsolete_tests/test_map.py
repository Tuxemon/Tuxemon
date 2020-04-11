from os.path import join
from unittest import TestCase
import mock
import pygame as pg

from tuxemon.core import prepare
from tuxemon.core.states.world import WorldState

pg.display.set_mode((1, 1), 0, 0)
control = mock.MagicMock()
state = WorldState(control)
map_name = join(prepare.BASEDIR, prepare.DATADIR, 'maps', 'test_cotton_town.tmx')
state.change_map(map_name)


class Test(TestCase):
    def test_long_path(self):
        path = state.pathfind(
            (1, 39),
            (36, 4),
        )
        expected = [
            (36, 4), (36, 5), (36, 6), (35, 6), (35, 7), (35, 8), (34, 8), (34, 9), (34, 10),
            (33, 10), (32, 10), (31, 10), (30, 10), (29, 10), (28, 10), (27, 10), (26, 10),
            (26, 11), (26, 12), (25, 12), (24, 12), (24, 13), (23, 13), (22, 13), (21, 13),
            (20, 13), (19, 13), (19, 14), (19, 15), (19, 16), (19, 17), (19, 18), (19, 19),
            (18, 19), (17, 19), (17, 20), (17, 21), (17, 22), (17, 23), (16, 23), (16, 24),
            (15, 24), (14, 24), (14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30),
            (14, 31), (14, 32), (14, 33), (14, 34), (14, 35), (14, 36), (14, 37), (14, 38),
            (14, 39), (13, 39), (12, 39), (11, 39), (10, 39), (9, 39), (8, 39), (7, 39),
            (6, 39), (5, 39), (4, 39), (3, 39), (2, 39),
        ]
        self.assertEqual(expected, path)

    def test_blocked_route(self):
        path = state.pathfind(
            (1, 39),
            (1, 21),
        )
        self.assertEquals(path, None)

    def test_out_of_bounds(self):
        path = state.pathfind(
            (1, 39),
            (-1, 0),
        )
        self.assertEquals(path, None)
