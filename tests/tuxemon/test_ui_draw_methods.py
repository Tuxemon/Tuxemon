# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.constants.paths import mods_folder
from tuxemon.tools import scale
from tuxemon.ui.draw import (
    RenderMode,
    blit_alpha,
    break_text_into_lines,
    build_line,
    calculate_alignment_offset,
    constrain_width,
    get_font_height,
    get_text_size,
    iter_render_text,
)
from tuxemon.ui.text import draw_text
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment

FONT_SIZE: int = prepare.FONT_SIZE
FONT_PATH = (
    mods_folder / "tuxemon/font" / Path(prepare.CONFIG.locale.font_file)
)


class TestIterRenderText(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.font = Font(FONT_PATH.as_posix(), scale(FONT_SIZE))
        self.font_large = Font(FONT_PATH.as_posix(), scale(FONT_SIZE + 1))
        self.fg = (0, 0, 0)  # Black
        self.bg = (255, 255, 255)  # White
        self.rect = Rect(0, 0, 200, 200)

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
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.LEFT,
            )
        )
        self.assertEqual(renders[0].rect.left, self.rect.left)

    def test_iter_render_text_center_alignment(self):
        text = "Center aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.CENTER,
            )
        )
        lines = list(constrain_width(text, self.font, self.rect.width))
        line_width = self.font.size(lines[0])[0]
        expected_left = (self.rect.width - line_width) // 2
        self.assertEqual(renders[0].rect.left, self.rect.left + expected_left)

    def test_iter_render_text_right_alignment(self):
        text = "Right aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.RIGHT,
            )
        )
        lines = list(constrain_width(text, self.font, self.rect.width))
        line_width = self.font.size(lines[0])[0]
        expected_left = self.rect.width - line_width
        self.assertEqual(renders[0].rect.left, self.rect.left + expected_left)

    def test_iter_render_text_top_alignment(self):
        text = "Top aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.LEFT,
                v_alignment=VerticalAlignment.TOP,
            )
        )
        self.assertEqual(renders[0].rect.top, self.rect.top)

    def test_iter_render_text_middle_alignment(self):
        text = "Middle aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.LEFT,
                v_alignment=VerticalAlignment.CENTER,
            )
        )
        line_height = get_font_height(self.font)
        lines = list(constrain_width(text, self.font, self.rect.width))
        total_text_height = len(lines) * line_height
        expected_top = (
            self.rect.top + (self.rect.height - total_text_height) // 2
        )
        self.assertEqual(renders[0].rect.top, expected_top)

    def test_iter_render_text_bottom_alignment(self):
        text = "Bottom aligned"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                h_alignment=HorizontalAlignment.LEFT,
                v_alignment=VerticalAlignment.BOTTOM,
            )
        )
        line_height = get_font_height(self.font)
        lines = list(constrain_width(text, self.font, self.rect.width))
        total_text_height = len(lines) * line_height
        expected_top = self.rect.top + self.rect.height - total_text_height
        self.assertEqual(renders[0].rect.top, expected_top)

    def test_iter_render_text_token_spacing(self):
        text = "Quick brown fox"
        renders = list(
            iter_render_text(
                text,
                self.font,
                self.fg,
                self.bg,
                self.rect,
                mode=RenderMode.TOKEN,
            )
        )

        tops = set(r.rect.top for r in renders)
        self.assertEqual(
            len(tops), 3, "Tokens should appear on separate lines"
        )

        for i in range(1, len(renders)):
            prev = renders[i - 1]
            curr = renders[i]

            if curr.rect.top == prev.rect.top:
                self.assertEqual(curr.rect.left, prev.rect.right)

        actual_text = " ".join([r.char for r in renders])
        self.assertEqual(actual_text, text)


class TestFontHeight(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.font = Font(FONT_PATH.as_posix(), scale(FONT_SIZE))
        self.font_large = Font(FONT_PATH.as_posix(), scale(FONT_SIZE + 1))

    def test_get_font_height(self):
        height = get_font_height(self.font)
        self.assertGreater(height, 0)

    def test_get_font_height_matches_get_text_size(self):
        height = get_font_height(self.font)
        width, height_guess = get_text_size("Tg", self.font)
        self.assertEqual(height, height_guess)

    def test_get_text_size(self):
        width, height = get_text_size("Test", self.font)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_get_text_size_single_character(self):
        width, height = get_text_size("A", self.font)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)


class TestConstrainWidth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.font = Font(FONT_PATH.as_posix(), scale(FONT_SIZE))
        self.font_large = Font(FONT_PATH.as_posix(), scale(FONT_SIZE + 1))

    def assertWrappedLines(
        self,
        text,
        font,
        width,
        expected_lines=None,
        min_lines=None,
        max_lines=None,
        strict_mode=False,
    ):
        lines = list(
            constrain_width(text, font, width, strict_mode=strict_mode)
        )
        if expected_lines is not None:
            self.assertEqual(len(lines), expected_lines)
        if min_lines is not None:
            self.assertGreaterEqual(len(lines), min_lines)
        if max_lines is not None:
            self.assertLessEqual(len(lines), max_lines)

    def test_constrain_width(self):
        text = "This is a test message"
        self.assertWrappedLines(text, self.font, 200, min_lines=1)

    def test_constrain_width_single_line(self):
        text = "This is a short message"
        self.assertWrappedLines(text, self.font, 200, min_lines=2, max_lines=4)

    def test_constrain_width_empty_string(self):
        text = ""
        self.assertWrappedLines(text, self.font, 200, expected_lines=1)

    def test_constrain_width_single_word(self):
        text = "This"
        self.assertWrappedLines(text, self.font, 200, expected_lines=1)

    def test_constrain_width_multiple_lines(self):
        text = "This is a test message that is too long for the width"
        self.assertWrappedLines(text, self.font, 100, min_lines=2)

    def test_strict_mode_true(self):
        text = "a" * 100
        with self.assertRaises(RuntimeError):
            list(constrain_width(text, self.font, 10))

    def test_strict_mode_false(self):
        text = "a" * 100
        lines = list(constrain_width(text, self.font, 10, False))
        self.assertEqual(lines, [text])

    def test_font_large_more_wraps(self):
        text = "This is a test message that is too long for the width"
        lines_regular = list(constrain_width(text, self.font, 200))
        lines_large = list(constrain_width(text, self.font_large, 200))
        self.assertGreater(len(lines_large), len(lines_regular))


class TestBlitAlphaFunction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.target_surface = pygame.display.set_mode((800, 600))
        self.source_surface = Surface((100, 100))
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

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.surface = Surface((400, 300))
        self.font = Font(FONT_PATH.as_posix(), scale(FONT_SIZE))
        self.font_large = Font(FONT_PATH.as_posix(), scale(FONT_SIZE + 1))
        self.rect = Rect(50, 50, 200, 100)
        self.font_color = (0, 0, 0)

    def test_draw_text_left_justify(self):
        text = "Left aligned"
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            h_alignment=HorizontalAlignment.LEFT,
            v_alignment=VerticalAlignment.TOP,
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
            h_alignment=HorizontalAlignment.CENTER,
            v_alignment=VerticalAlignment.CENTER,
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

        expected_x = max(0, min(expected_x, self.surface.get_width() - 1))
        expected_y = max(0, min(expected_y, self.surface.get_height() - 1))

        try:
            pixel = self.surface.get_at((expected_x, expected_y))
            self.assertEqual(pixel[:3], self.font_color)
        except IndexError:
            self.fail(
                f"Blit position out of bounds: ({expected_x}, {expected_y})"
            )

    def test_draw_text_right_justify(self):
        text = "Right aligned"
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            h_alignment=HorizontalAlignment.RIGHT,
            v_alignment=VerticalAlignment.BOTTOM,
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

        expected_x = max(0, min(expected_x, self.surface.get_width() - 1))
        expected_y = max(0, min(expected_y, self.surface.get_height() - 1))

        try:
            pixel = self.surface.get_at((expected_x, expected_y))
            self.assertEqual(pixel[:3], self.font_color)
        except IndexError:
            self.fail(
                f"Blit position out of bounds: ({expected_x}, {expected_y})"
            )

    def test_draw_text_empty(self):
        text = ""
        draw_text(
            surface=self.surface,
            text=text,
            rect=self.rect,
            h_alignment=HorizontalAlignment.LEFT,
            v_alignment=VerticalAlignment.TOP,
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
            h_alignment=HorizontalAlignment.LEFT,
            v_alignment=VerticalAlignment.TOP,
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


class TestBreakTextIntoLines(unittest.TestCase):

    @patch("tuxemon.ui.draw.get_text_size")
    def test_empty_text(self, mock_get_text_size):
        text = ""
        mock_get_text_size.return_value = (0, 0)
        result = list(break_text_into_lines(text, None, 100))
        self.assertEqual(result, [""])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_single_word(self, mock_get_text_size):
        text = "Hello"
        mock_get_text_size.return_value = (50, 20)
        result = list(break_text_into_lines(text, None, 100))
        self.assertEqual(result, ["Hello"])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_single_word_exceeding_max_width(self, mock_get_text_size):
        text = "Hello"
        mock_get_text_size.return_value = (150, 20)
        result = list(
            break_text_into_lines(text, None, 100, allow_word_overflow=False)
        )
        self.assertEqual(result, ["Hello"])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_multiple_words(self, mock_get_text_size):
        text = "Hello World"
        mock_get_text_size.side_effect = [
            (50, 20),  # "Hello"
            (90, 20),  # "Hello World"
        ]
        result = list(break_text_into_lines(text, None, 100))
        self.assertEqual(result, ["Hello World"])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_multiple_words_exceeding_max_width(self, mock_get_text_size):
        text = "Hello verylongword"
        mock_get_text_size.side_effect = [
            (50, 20),  # "Hello"
            (120, 20),  # "Hello verylongword"
        ]
        result = list(break_text_into_lines(text, None, 100))
        self.assertEqual(result, ["Hello", "verylongword"])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_paragraph_break(self, mock_get_text_size):
        text = "Hello World\nThis is another paragraph"
        mock_get_text_size.side_effect = [
            (90, 20),  # "Hello World"
            (0, 0),  # "\n"
            (40, 20),  # "This"
            (60, 20),  # "This is"
            (100, 20),  # "This is another"
            (140, 20),  # "This is another paragraph"
        ]
        result = list(break_text_into_lines(text, None, 140))
        self.assertTrue(
            set(result) == set(["Hello World", "This is another paragraph"])
        )

    @patch("tuxemon.ui.draw.get_text_size")
    def test_allow_word_overflow(self, mock_get_text_size):
        text = "verylongword"
        mock_get_text_size.return_value = (150, 20)
        result = list(
            break_text_into_lines(text, None, 100, allow_word_overflow=True)
        )
        self.assertEqual(result, ["verylongword"])

    @patch("tuxemon.ui.draw.get_text_size")
    def test_strip_leading_trailing_whitespace(self, mock_get_text_size):
        text = "   Hello World   "
        mock_get_text_size.return_value = (90, 20)
        result = list(break_text_into_lines(text, None, 100))
        self.assertEqual(result, ["Hello World"])


class TestCalculateAlignmentOffset(unittest.TestCase):

    def setUp(self):
        self.container_rect = Rect(0, 0, 100, 100)
        self.content_width = 50
        self.content_height = 50

    def test_left_top_alignment(self):
        h_alignment = HorizontalAlignment.LEFT
        v_alignment = VerticalAlignment.TOP
        expected_offset = (0, 0)
        self.assertEqual(
            calculate_alignment_offset(
                self.container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_center_center_alignment(self):
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        expected_offset = (25, 25)
        self.assertEqual(
            calculate_alignment_offset(
                self.container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_right_bottom_alignment(self):
        h_alignment = HorizontalAlignment.RIGHT
        v_alignment = VerticalAlignment.BOTTOM
        expected_offset = (50, 50)
        self.assertEqual(
            calculate_alignment_offset(
                self.container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_content_larger_than_container(self):
        content_width = 150
        content_height = 150
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        expected_offset = (0, 0)
        self.assertEqual(
            calculate_alignment_offset(
                self.container_rect,
                content_width,
                content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_content_equal_to_container(self):
        content_width = 100
        content_height = 100
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        expected_offset = (0, 0)
        self.assertEqual(
            calculate_alignment_offset(
                self.container_rect,
                content_width,
                content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_container_zero_width(self):
        container_rect = Rect(0, 0, 0, 100)
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        expected_offset = (0, 0)
        self.assertEqual(
            calculate_alignment_offset(
                container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_container_zero_height(self):
        container_rect = Rect(0, 0, 100, 0)
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        expected_offset = (0, 0)
        self.assertEqual(
            calculate_alignment_offset(
                container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            ),
            expected_offset,
        )

    def test_negative_content_dimensions(self):
        content_width = -50
        content_height = -50
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        with self.assertRaises(ValueError):
            calculate_alignment_offset(
                self.container_rect,
                content_width,
                content_height,
                h_alignment,
                v_alignment,
            )

    def test_negative_container_dimensions(self):
        container_rect = Rect(0, 0, -100, -100)
        h_alignment = HorizontalAlignment.CENTER
        v_alignment = VerticalAlignment.CENTER
        with self.assertRaises(ValueError):
            calculate_alignment_offset(
                container_rect,
                self.content_width,
                self.content_height,
                h_alignment,
                v_alignment,
            )
