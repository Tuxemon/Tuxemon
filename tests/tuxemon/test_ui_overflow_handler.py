# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from unittest.mock import Mock

import pygame
from pygame.font import Font
from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.constants.paths import mods_folder
from tuxemon.tools import scale
from tuxemon.ui.draw import OverflowHandler, RenderedChar, TextOverflow
from tuxemon.ui.text_renderer import TextRenderer

FONT_SIZE: int = prepare.FONT_SIZE
FONT_PATH = (
    mods_folder / "tuxemon/font" / Path(prepare.CONFIG.locale.font_file)
)


class TestOverflowHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.font = Font(FONT_PATH.as_posix(), scale(FONT_SIZE))
        self.rect = Rect(0, 0, 100, 100)
        self.behavior = TextOverflow.ELLIPSIS
        self.renderer = Mock(spec=TextRenderer)
        self.handler = OverflowHandler(self.font, self.rect, self.behavior)

    def test_init(self):
        self.assertEqual(self.handler.font, self.font)
        self.assertEqual(self.handler.rect, self.rect)
        self.assertEqual(self.handler.behavior, self.behavior)
        self.assertEqual(self.handler.ellipsis, "…")
        self.assertEqual(self.handler.ellipsis_width, scale(prepare.FONT_SIZE))

    def test_get_ellipsis_char(self):
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        surface = Mock()
        surface.get_rect.return_value.top = top
        renderer.shadow_text.return_value = surface
        rendered_char = self.handler.get_ellipsis_char(top, fg, bg, renderer)
        self.assertIsInstance(rendered_char, RenderedChar)
        self.assertEqual(rendered_char.rect.top, top)
        renderer.shadow_text.assert_called_once_with(
            "…", bg=(0, 0, 0), fg=(255, 255, 255)
        )

    def test_handle_render_attempt_expand(self):
        self.handler.behavior = TextOverflow.EXPAND
        current_x_position = 50
        segment_width = 20
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertTrue(should_render)
        self.assertIsNone(optional_ellipsis)

    def test_handle_render_attempt_fits(self):
        current_x_position = 50
        segment_width = 20
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertTrue(should_render)
        self.assertIsNone(optional_ellipsis)

    def test_handle_render_attempt_does_not_fit_ellipsis(self):
        current_x_position = self.rect.right - self.handler.ellipsis_width
        segment_width = 30
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        surface = Mock()
        surface.get_rect.return_value.top = top
        renderer.shadow_text.return_value = surface
        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertFalse(should_render)
        self.assertIsNotNone(optional_ellipsis)

    def test_handle_render_attempt_does_not_fit_no_ellipsis(self):
        current_x_position = 120
        segment_width = 20
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertFalse(should_render)
        self.assertIsNone(optional_ellipsis)

    def test_handle_render_attempt_ellipsis_fits(self):
        ellipsis_width = self.handler.ellipsis_width
        current_x_position = self.rect.right - ellipsis_width - 5
        segment_width = 50
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer

        surface = Mock()
        surface.get_rect.return_value.top = top
        renderer.shadow_text.return_value = surface

        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertFalse(should_render)
        self.assertIsNotNone(optional_ellipsis)

    def test_handle_render_attempt_clip(self):
        self.handler.behavior = TextOverflow.CLIP
        current_x_position = 120
        segment_width = 20
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer

        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertFalse(should_render)
        self.assertIsNone(optional_ellipsis)

    def test_ellipsis_exact_fit(self):
        current_x_position = self.rect.right - self.handler.ellipsis_width
        segment_width = 50  # Doesn’t matter here
        top = 10
        fg = (255, 255, 255)
        bg = (0, 0, 0)
        renderer = self.renderer
        surface = Mock()
        surface.get_rect.return_value.top = top
        renderer.shadow_text.return_value = surface

        should_render, optional_ellipsis = self.handler.handle_render_attempt(
            current_x_position, segment_width, top, fg, bg, renderer
        )
        self.assertFalse(should_render)
        self.assertIsNotNone(optional_ellipsis)
