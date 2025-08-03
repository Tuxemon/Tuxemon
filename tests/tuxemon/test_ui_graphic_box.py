# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

import pygame
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.ui.graphic_box import GraphicBox, TileLayout


class TestTileLayout(unittest.TestCase):

    def test_init(self):
        image = Surface((9, 9))
        layout = TileLayout(image)
        self.assertEqual(layout.grid_size, 3)
        self.assertIsInstance(layout.tiles, dict)

    def test_init_with_custom_grid_size(self):
        image = Surface((12, 12))
        layout = TileLayout(image, grid_size=4)
        self.assertEqual(layout.grid_size, 4)
        self.assertIsInstance(layout.tiles, dict)

    def test_extract_tiles(self):
        image = Surface((9, 9))
        layout = TileLayout(image)
        self.assertEqual(len(layout.tiles), 9)

    def test_init_with_custom_grid_size(self):
        image = Surface((12, 12))
        layout = TileLayout(image, grid_size=3)
        self.assertEqual(layout.grid_size, 3)

    def test_extract_tiles_invalid_image_size(self):
        image = Surface((10, 9))
        with self.assertRaises(ValueError):
            TileLayout(image)

    def test_extract_tiles_with_custom_grid_size(self):
        image = Surface((12, 12))
        layout = TileLayout(image, grid_size=3)
        self.assertEqual(len(layout.tiles), 9)

    def test_extract_tiles_empty_image(self):
        image = Surface((0, 0))
        with self.assertRaises(ValueError):
            TileLayout(image)

    def test_extract_tiles_image_with_zero_grid_size(self):
        image = Surface((9, 9))
        with self.assertRaises(ValueError):
            TileLayout(image, grid_size=0)


class TestGraphicBox(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.surface = pygame.display.set_mode((800, 600))

    def test_init(self):
        box = GraphicBox()
        self.assertIsNone(box._background)
        self.assertIsNone(box._color)
        self.assertFalse(box._fill_tiles)
        self.assertEqual(box._tiles, {})
        self.assertEqual(box._tile_size, (0, 0))

    def test_set_border(self):
        image = Surface((12, 12))
        box = GraphicBox()
        box._set_border(image)
        self.assertEqual(box._tile_size, (4, 4))

    def test_set_border_invalid_size(self):
        image = Surface((10, 12))
        box = GraphicBox()
        with self.assertRaises(ValueError):
            box._set_border(image)

    def test_calc_inner_rect(self):
        box = GraphicBox()
        rect = Rect(0, 0, 100, 100)
        inner_rect = box.calc_inner_rect(rect)
        self.assertEqual(inner_rect, rect)

        box._tiles = [Surface((10, 10))]
        box._tile_size = (10, 10)
        inner_rect = box.calc_inner_rect(rect)
        self.assertEqual(inner_rect, Rect(10, 10, 80, 80))

    def test_draw(self):
        box = GraphicBox()
        rect = Rect(0, 0, 100, 100)
        box._draw(self.surface, rect)

        box._background = Surface((100, 100))
        box._draw(self.surface, rect)

        box._color = (255, 0, 0)
        box._draw(self.surface, rect)

    def test_update_image(self):
        box = GraphicBox()
        box._rect = Rect(0, 0, 100, 100)
        box.update_image()
        self.assertIsNotNone(box.image)
