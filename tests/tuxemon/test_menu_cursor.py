# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

import pygame

from tuxemon.menu.cursor import MenuCursorController
from tuxemon.sprite import SpriteGroup


class TestMenuCursorController(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((0, 0))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.cursor_filename = "gfx/arrow.png"
        self.menu_sprites = SpriteGroup()
        self.get_selected_item = MagicMock(return_value=None)
        self.animate = MagicMock(return_value=None)
        self.duration = 1.0
        self.remove_animations = MagicMock()
        self.controller = MenuCursorController(
            self.cursor_filename,
            self.menu_sprites,
            self.get_selected_item,
            self.animate,
            self.duration,
            self.remove_animations,
        )
        self.arrow = self.controller.arrow
        self.sprites = self.controller.sprites

    def test_init(self):
        self.assertIsNotNone(self.controller.arrow)
        self.assertEqual(self.controller.sprites, self.menu_sprites)
        self.assertEqual(self.controller.get_item, self.get_selected_item)
        self.assertEqual(self.controller.animate, self.animate)
        self.assertEqual(self.controller.duration, self.duration)
        self.assertEqual(
            self.controller.remove_animations, self.remove_animations
        )

    def test_get_margin(self):
        margin = self.controller.get_margin()
        self.assertIsInstance(margin, tuple)
        self.assertEqual(len(margin), 2)

    def test_show_cursor(self):
        self.controller.hide_cursor()
        self.controller.show_cursor()
        self.assertIn(self.arrow, self.sprites)

    def test_hide_cursor(self):
        self.controller.show_cursor()
        self.controller.hide_cursor()
        self.assertNotIn(self.arrow, self.sprites)

    def test_trigger_cursor_update_animated(self):
        item = MagicMock()
        item.rect.midleft = (10, 20)
        self.get_selected_item.return_value = item
        animation = self.controller.trigger_cursor_update(animate=True)
        self.assertIsNone(animation)
        self.animate.assert_called_once()
        self.remove_animations.assert_called_once_with(
            self.controller.arrow.rect
        )

    def test_trigger_cursor_update_not_animated(self):
        item = MagicMock()
        item.rect.midleft = (10, 20)
        self.get_selected_item.return_value = item
        animation = self.controller.trigger_cursor_update(animate=False)
        self.assertIsNone(animation)
        self.animate.assert_not_called()

    def test_update_selection_focus(self):
        previous_item = MagicMock()
        new_item = MagicMock()
        self.controller.update_selection_focus(previous_item, new_item)
        previous_item.in_focus = False
        new_item.in_focus = True
        previous_item.update_image.assert_called_once()
        new_item.update_image.assert_called_once()

    def test_update_focus(self):
        item = MagicMock()
        self.controller._update_focus(item, True)
        item.in_focus = True
        item.update_image.assert_called_once()

    def test_ensure_cursor_visible(self):
        self.controller._ensure_cursor_visible(True)
        self.assertIn(self.arrow, self.sprites)
        self.controller._ensure_cursor_visible(False)
        self.assertNotIn(self.arrow, self.sprites)

    def test_trigger_cursor_update_no_item(self):
        self.get_selected_item.return_value = None
        animation = self.controller.trigger_cursor_update(animate=True)
        self.assertIsNone(animation)

    def test_update_selection_focus_no_previous_item(self):
        new_item = MagicMock()
        self.controller.update_selection_focus(None, new_item)
        new_item.in_focus = True
        new_item.update_image.assert_called_once()

    def test_update_selection_focus_no_new_item(self):
        previous_item = MagicMock()
        self.controller.update_selection_focus(previous_item, None)
        previous_item.in_focus = False
        previous_item.update_image.assert_called_once()

    def test_ensure_cursor_visible_already_visible(self):
        self.controller.show_cursor()
        self.controller._ensure_cursor_visible(True)
        self.assertIn(self.arrow, self.sprites)

    def test_ensure_cursor_visible_already_hidden(self):
        self.controller.hide_cursor()
        self.controller._ensure_cursor_visible(False)
        self.assertNotIn(self.arrow, self.sprites)
