# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import unittest

import pygame
from pygame import Rect

from tuxemon.ui.draw import (
    GraphicBox,
    blit_alpha,
    build_line,
    constrain_width,
    guess_rendered_text_size,
    guest_font_height,
    iter_render_text,
    layout,
    shadow_text,
)
from tuxemon.ui.text import draw_text


class TestGraphicBox(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.surface = pygame.display.set_mode((800, 600))

    def test_init(self):
        box = GraphicBox()
        self.assertIsNone(box._background)
        self.assertIsNone(box._color)
        self.assertFalse(box._fill_tiles)
        self.assertEqual(box._tiles, [])
        self.assertEqual(box._tile_size, (0, 0))

    def test_set_border(self):
        image = pygame.Surface((12, 12))
        box = GraphicBox()
        box._set_border(image)
        self.assertEqual(box._tile_size, (4, 4))

    def test_set_border_invalid_size(self):
        image = pygame.Surface((10, 12))
        box = GraphicBox()
        with self.assertRaises(ValueError):
            box._set_border(image)

    def test_calc_inner_rect(self):
        box = GraphicBox()
        rect = Rect(0, 0, 100, 100)
        inner_rect = box.calc_inner_rect(rect)
        self.assertEqual(inner_rect, rect)

        box._tiles = [pygame.Surface((10, 10))]
        box._tile_size = (10, 10)
        inner_rect = box.calc_inner_rect(rect)
        self.assertEqual(inner_rect, Rect(10, 10, 80, 80))

    def test_draw(self):
        box = GraphicBox()
        rect = Rect(0, 0, 100, 100)
        box._draw(self.surface, rect)

        box._background = pygame.Surface((100, 100))
        box._draw(self.surface, rect)

        box._color = (255, 0, 0)
        box._draw(self.surface, rect)

    def test_update_image(self):
        box = GraphicBox()
        box._rect = Rect(0, 0, 100, 100)
        box.update_image()
        self.assertIsNotNone(box.image)


class TestIterRenderText(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.font = pygame.font.SysFont("Arial", 24)
        self.fg = (0, 0, 0)  # Black
        self.bg = (255, 255, 255)  # White
        self.rect = pygame.Rect(0, 0, 200, 200)

    def test_iter_render_text(self):
        text = "This is a test message"
        renders = list(
            iter_render_text(text, self.font, self.fg, self.bg, self.rect)
        )
        self.assertGreater(len(renders), 0)

    def test_iter_render_text_empty_string(self):
        text = ""
        renders = list(
            iter_render_text(text, self.font, self.fg, self.bg, self.rect)
        )
        self.assertEqual(len(renders), 0)

    def test_iter_render_text_single_line(self):
        text = "This is a short message"
        renders = list(
            iter_render_text(text, self.font, self.fg, self.bg, self.rect)
        )
        self.assertGreater(len(renders), 0)

    def test_iter_render_text_single_word(self):
        text = "This"
        renders = list(
            iter_render_text(text, self.font, self.fg, self.bg, self.rect)
        )
        self.assertEqual(len(renders), len(list(build_line(text))))

    def test_iter_render_text_skips_trailing_spaces(self):
        text = "This is a test message "
        renders = list(
            iter_render_text(text, self.font, self.fg, self.bg, self.rect)
        )
        self.assertEqual(
            len(renders),
            len(
                list(
                    iter_render_text(
                        text.strip(), self.font, self.fg, self.bg, self.rect
                    )
                )
            ),
        )

    def test_iter_render_text_left_alignment(self):
        text = "Left aligned"
        renders = list(
            iter_render_text(
                text, self.font, self.fg, self.bg, self.rect, alignment="left"
            )
        )
        self.assertEqual(renders[0][0].left, self.rect.left)

    def test_iter_render_text_center_alignment(self):
        text = "Center aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                alignment="center",
            )
        )
        expected_left = (self.rect.width - self.font.size(text)[0]) // 2
        self.assertEqual(renders[0][0].left, self.rect.left + expected_left)

    def test_iter_render_text_right_alignment(self):
        text = "Right aligned"
        renders = list(
            iter_render_text(
                text, self.font, self.fg, self.bg, self.rect, alignment="right"
            )
        )
        expected_left = self.rect.width - self.font.size(text)[0]
        self.assertEqual(renders[0][0].left, self.rect.left + expected_left)

    def test_iter_render_text_top_alignment(self):
        text = "Top aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                alignment="left",
                vertical_alignment="top",
            )
        )
        self.assertEqual(renders[0][0].top, self.rect.top)

    def test_iter_render_text_middle_alignment(self):
        text = "Middle aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                alignment="left",
                vertical_alignment="middle",
            )
        )
        total_text_height = self.font.size(text)[1]
        expected_top = (
            self.rect.top + (self.rect.height - total_text_height) // 2
        )
        self.assertEqual(renders[0][0].top, expected_top)

    def test_iter_render_text_bottom_alignment(self):
        text = "Bottom aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                alignment="left",
                vertical_alignment="bottom",
            )
        )
        total_text_height = self.font.size(text)[1]
        expected_top = self.rect.top + self.rect.height - total_text_height
        self.assertEqual(renders[0][0].top, expected_top)


class TestShadowText(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.font = pygame.font.SysFont("Arial", 24)
        self.fg = (0, 0, 0)  # Black
        self.bg = (255, 255, 255)  # White

    def test_shadow_text(self):
        text = "Test"
        image = shadow_text(self.font, self.fg, self.bg, text)
        self.assertIsNotNone(image)

    def test_shadow_text_size(self):
        text = "Test"
        image = shadow_text(self.font, self.fg, self.bg, text)
        top = self.font.render(text, True, self.fg)
        offset = layout((0.5, 0.5))
        size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
        self.assertEqual(image.get_size(), tuple(size))

    def test_shadow_text_empty_string(self):
        text = ""
        image = shadow_text(self.font, self.fg, self.bg, text)
        self.assertIsNotNone(image)

    def test_shadow_text_single_character(self):
        text = "A"
        image = shadow_text(self.font, self.fg, self.bg, text)
        self.assertIsNotNone(image)


class TestFontHeight(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.font = pygame.font.SysFont("Arial", 24)

    def test_guest_font_height(self):
        height = guest_font_height(self.font)
        self.assertGreater(height, 0)

    def test_guest_font_height_matches_guess_rendered_text_size(self):
        height = guest_font_height(self.font)
        width, height_guess = guess_rendered_text_size("Tg", self.font)
        self.assertEqual(height, height_guess)

    def test_guess_rendered_text_size(self):
        width, height = guess_rendered_text_size("Test", self.font)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_guess_rendered_text_size_single_character(self):
        width, height = guess_rendered_text_size("A", self.font)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)


class TestConstrainWidth(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.font = pygame.font.SysFont("Arial", 24)

    def test_constrain_width(self):
        text = "This is a test message"
        width = 200
        lines = list(constrain_width(text, self.font, width))
        self.assertGreater(len(lines), 0)

    def test_constrain_width_single_line(self):
        text = "This is a short message"
        width = 200
        lines = list(constrain_width(text, self.font, width))
        self.assertEqual(len(lines), 2)

    def test_constrain_width_empty_string(self):
        text = ""
        width = 200
        lines = list(constrain_width(text, self.font, width))
        self.assertEqual(len(lines), 1)

    def test_constrain_width_single_word(self):
        text = "This"
        width = 200
        lines = list(constrain_width(text, self.font, width))
        self.assertEqual(len(lines), 1)

    def test_constrain_width_multiple_lines(self):
        text = "This is a test message that is too long for the width"
        width = 100
        lines = list(constrain_width(text, self.font, width))
        self.assertGreater(len(lines), 1)

    def test_runtime_error(self):
        text = "a" * 100
        width = 10
        with self.assertRaises(RuntimeError):
            list(constrain_width(text, self.font, width))


class TestBlitAlphaFunction(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.target_surface = pygame.display.set_mode((800, 600))
        self.source_surface = pygame.Surface((100, 100))
        self.source_surface.fill((255, 0, 0))

    def test_blit_alpha(self):
        blit_alpha(self.target_surface, self.source_surface, (0, 0), 255)
        self.assertEqual(self.target_surface.get_at((0, 0)), (255, 0, 0))

        self.target_surface.fill((0, 0, 0))
        blit_alpha(self.target_surface, self.source_surface, (0, 0), 128)
        self.assertEqual(self.target_surface.get_at((0, 0)).r, 127)
        self.assertEqual(self.target_surface.get_at((0, 0)).g, 0)
        self.assertEqual(self.target_surface.get_at((0, 0)).b, 0)

        self.target_surface.fill((0, 0, 0))
        blit_alpha(self.target_surface, self.source_surface, (0, 0), 0)
        self.assertEqual(self.target_surface.get_at((0, 0)), (0, 0, 0))

    def test_blit_alpha_out_of_range_opacity(self):
        self.target_surface.fill((0, 0, 0))
        blit_alpha(self.target_surface, self.source_surface, (0, 0), 256)
        self.assertEqual(self.target_surface.get_at((0, 0)), (255, 0, 0))

        self.target_surface.fill((0, 0, 0))
        blit_alpha(self.target_surface, self.source_surface, (0, 0), -1)
        self.assertEqual(self.target_surface.get_at((0, 0)), (0, 0, 0))


class TestDrawText(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.surface = pygame.Surface((400, 300))
        self.font = pygame.font.SysFont("Arial", 24)
        self.rect = pygame.Rect(50, 50, 200, 100)
        self.font_color = (0, 0, 0)

    def tearDown(self):
        pygame.quit()

    def test_draw_text_left_justify(self):
        text = "Left aligned"
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            justify="left",
            align="top",
            font=self.font,
            font_color=self.font_color,
        )
        self.assertEqual(
            self.surface.get_at((self.rect.left, self.rect.top)),
            self.font_color,
        )

    def test_draw_text_center_justify(self):
        text = "Center aligned"
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            justify="center",
            align="middle",
            font=self.font,
            font_color=self.font_color,
        )

        rendered_text = self.font.render(text, True, self.font_color)
        expected_x = (
            self.rect.left + (self.rect.width - rendered_text.get_width()) // 2
        )
        expected_y = (
            self.rect.top
            + (self.rect.height - rendered_text.get_height()) // 2
        )
        self.assertEqual(
            self.surface.get_at((expected_x, expected_y)), self.font_color
        )

    def test_draw_text_right_justify(self):
        text = "Right aligned"
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            justify="right",
            align="bottom",
            font=self.font,
            font_color=self.font_color,
        )

        rendered_text = self.font.render(text, True, self.font_color)
        expected_x = (
            self.rect.left + self.rect.width - rendered_text.get_width()
        )
        expected_y = (
            self.rect.top + self.rect.height - rendered_text.get_height()
        )
        self.assertEqual(
            self.surface.get_at((expected_x, expected_y)), self.font_color
        )

    def test_draw_text_empty(self):
        text = ""
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            justify="left",
            align="top",
            font=self.font,
            font_color=self.font_color,
        )
        self.assertEqual(
            self.surface.get_at((self.rect.left, self.rect.top)),
            self.surface.get_at((0, 0)),
        )

    def test_draw_text_word_wrapping(self):
        text = "This is a very long text that should wrap inside the rectangle area."
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            justify="left",
            align="top",
            font=self.font,
            font_color=self.font_color,
        )

        lines = text.split()
        wrapped_text = []
        current_line = ""
        for word in lines:
            if self.font.size(current_line + " " + word)[0] > self.rect.width:
                wrapped_text.append(current_line)
                current_line = word
            else:
                current_line += " " + word
        wrapped_text.append(current_line.strip())
        self.assertGreater(len(wrapped_text), 1)
