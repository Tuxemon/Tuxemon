# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

import pygame
from pygame.surface import Surface

from tuxemon.ui.text import MultilineTextRenderer
from tuxemon.ui.text_renderer import TextRenderer


class TestMultilineTextRenderer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.text_renderer = TextRenderer((255, 255, 255))
        self.multiline_text_renderer = MultilineTextRenderer(
            self.text_renderer
        )

    def test_init(self):
        self.assertEqual(
            self.multiline_text_renderer.text_renderer, self.text_renderer
        )
        self.assertEqual(self.multiline_text_renderer.line_spacing, 0)

    def test_render_lines_single_line(self):
        lines = self.multiline_text_renderer.render_lines(
            "Hello, World!", 1000
        )
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 1)
        self.assertIsInstance(lines[0][0], Surface)

    def test_render_lines_multiple_lines(self):
        lines = self.multiline_text_renderer.render_lines(
            "Hello, World! This is a test.", 10
        )
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 1)
        for line, _ in lines:
            self.assertIsInstance(line, Surface)

    def test_render_lines_max_width(self):
        lines = self.multiline_text_renderer.render_lines(
            "Hello, World! This is a test.", 50
        )
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 1)
        for line, _ in lines:
            self.assertIsInstance(line, Surface)

    def test_render_lines_line_spacing(self):
        multiline_text_renderer = MultilineTextRenderer(
            self.text_renderer, line_spacing=10
        )
        lines = multiline_text_renderer.render_lines(
            "Hello, World! This is a test.", 1000
        )
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 1)
        self.assertIsInstance(lines[0][0], Surface)

    def test_render_lines_single_character(self):
        lines = self.multiline_text_renderer.render_lines("a", 1000)
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 1)
        self.assertIsInstance(lines[0][0], Surface)

    def test_render_lines_non_ascii_characters(self):
        lines = self.multiline_text_renderer.render_lines("éàü", 1000)
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 1)
        self.assertIsInstance(lines[0][0], Surface)

    def test_render_lines_surface_size(self):
        lines = self.multiline_text_renderer.render_lines(
            "Hello, World!", 1000
        )
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 1)
        self.assertGreater(lines[0][0].get_width(), 0)
        self.assertGreater(lines[0][1], 0)

    def test_render_lines_empty_string(self):
        lines = self.multiline_text_renderer.render_lines("", 1000)
        self.assertIsInstance(lines, list)
        self.assertEqual(len(lines), 0)

    def test_render_lines_long_string(self):
        lines = self.multiline_text_renderer.render_lines("a" * 1000, 1000)
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 0)

    def test_render_lines_newline(self):
        lines = self.multiline_text_renderer.render_lines(
            "Hello, World!\\nThis is a test.", 1000
        )
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 1)
