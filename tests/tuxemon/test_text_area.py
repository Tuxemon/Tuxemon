# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

import pygame

from tuxemon.ui.draw import (
    TextOverflow,
    iter_render_text,
)
from tuxemon.ui.text import TextArea
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment
from tuxemon.ui.text_renderer import TextRenderer


class DummyChar:
    def __init__(self, ch="X"):
        self.surface = pygame.Surface((1, 1))
        self.rect = self.surface.get_rect()


def dummy_iter_render_text(**kwargs):
    for _ in kwargs["text"]:
        yield DummyChar()


class TestTextArea(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        font = pygame.font.Font(None, 16)
        self.text_area = TextArea(font=font, font_color=(255, 255, 255))
        self.text_area._iter = None

    def test_initial_state(self):
        self.assertEqual(self.text_area.text, "")
        self.assertFalse(self.text_area.drawing_text)

    def test_text_setter_triggers_animation(self):
        self.text_area._start_text_animation = lambda: setattr(
            self.text_area, "drawing_text", True
        )
        self.text_area.text = "Hello"
        self.assertEqual(self.text_area.text, "Hello")
        self.assertTrue(self.text_area.drawing_text)

    def test_len_returns_length(self):
        self.text_area.text = "abc"
        self.assertEqual(len(self.text_area), 3)

    def test_iter_and_next(self):
        self.text_area._iter = iter([DummyChar(), DummyChar()])
        self.text_area.animated = True
        self.text_area.drawing_text = True
        next(self.text_area)
        self.assertTrue(self.text_area.drawing_text)
        with self.assertRaises(StopIteration):
            while True:
                next(self.text_area)
        self.assertFalse(self.text_area.drawing_text)

    def test_non_animated_text_sets_image_directly(self):
        self.text_area.animated = False
        self.text_area.text = "Direct"
        self.assertIsNotNone(self.text_area.image)

    def test_set_background_color(self):
        self.text_area.rect = pygame.Rect(0, 0, 10, 10)
        self.text_area.set_background(background_color=(255, 0, 0))
        self.assertEqual(
            self.text_area.image.get_at((0, 0)), pygame.Color(255, 0, 0, 255)
        )

    def test_set_background_image(self):
        surf = pygame.Surface((10, 10))
        surf.fill((0, 255, 0))
        self.text_area.rect = pygame.Rect(0, 0, 10, 10)
        self.text_area.set_background(background_image=surf)
        self.assertEqual(
            self.text_area.image.get_at((0, 0)), pygame.Color(0, 255, 0, 255)
        )

    def test_overflow_behavior_setter(self):
        self.text_area.set_overflow_behavior(TextOverflow.WRAP)
        self.assertEqual(self.text_area.overflow_behavior, TextOverflow.WRAP)

    def test_start_text_animation_resets_surface(self):
        self.text_area.rect = pygame.Rect(0, 0, 10, 10)
        global iter_render_text
        old_iter = iter_render_text
        iter_render_text = dummy_iter_render_text
        try:
            self.text_area.text = "abc"
            self.assertTrue(self.text_area.drawing_text)
            self.assertIsNotNone(self.text_area._iter)
        finally:
            iter_render_text = old_iter

    def test_next_raises_stopiteration_when_not_animated(self):
        self.text_area.animated = False
        with self.assertRaises(StopIteration):
            next(self.text_area)

    def test_text_setter_same_value_does_not_restart_animation(self):
        self.text_area.text = "abc"
        self.text_area.drawing_text = False
        self.text_area.text = "abc"
        self.assertFalse(self.text_area.drawing_text)


class TestTextAreaStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        font = pygame.font.Font(None, 16)
        self.text_area = TextArea(font=font, font_color=(255, 255, 255))
        self.text_area.rect = pygame.Rect(0, 0, 100, 20)

    def test_fast_click_before_update(self):
        self.text_area.text = "FastClick"
        self.text_area.drawing_text = True
        for _ in self.text_area:
            pass
        self.assertFalse(self.text_area.drawing_text)
        self.assertEqual(self.text_area.text, "FastClick")

    def test_update_progressive_render(self):
        self.text_area.text = "Hello"
        self.text_area.drawing_text = True
        try:
            while True:
                next(self.text_area)
        except StopIteration:
            pass
        self.assertFalse(self.text_area.drawing_text)

    def test_empty_string(self):
        self.text_area.text = ""
        self.assertFalse(self.text_area.drawing_text)
        self.assertEqual(self.text_area.text, "")

    def test_repeated_text_changes(self):
        for msg in ["One", "Two", "Three"]:
            self.text_area.text = msg
            for _ in self.text_area:
                pass
            self.assertEqual(self.text_area.text, msg)
            self.assertFalse(self.text_area.drawing_text)

    def test_surface_size_zero(self):
        ta = TextArea(
            font=pygame.font.Font(None, 16), font_color=(255, 255, 255)
        )
        ta.rect = pygame.Rect(0, 0, 0, 0)
        ta.text = "ZeroRect"
        self.assertTrue(ta.drawing_text or ta.text == "ZeroRect")

    def test_drawing_text_stays_true_until_stopiteration(self):
        self.text_area.text = "Hello"
        self.assertTrue(self.text_area.drawing_text)

        count = 0
        try:
            while True:
                next(self.text_area)
                count += 1
                self.assertTrue(self.text_area.drawing_text)
        except StopIteration:
            pass

        self.assertEqual(count, len(self.text_area.text))
        self.assertFalse(self.text_area.drawing_text)

    def test_non_animated_text_is_fully_rendered_immediately(self):
        self.text_area.animated = False
        self.text_area.text = "Static Text"
        self.assertEqual(self.text_area.text, "Static Text")
        self.assertFalse(self.text_area.drawing_text)

    def test_len_after_setting_empty_text(self):
        self.text_area.text = "A B C"
        self.assertEqual(len(self.text_area), 5)
        self.text_area.text = ""
        self.assertEqual(len(self.text_area), 0)

    def test_next_on_completed_text_raises_stopiteration(self):
        self.text_area.animated = True
        self.text_area.drawing_text = False

        with self.assertRaises(StopIteration):
            next(self.text_area)

    def test_empty_string_animation_state(self):
        self.text_area.animated = True
        self.text_area.text = "Testing"
        self.assertTrue(self.text_area.drawing_text)

        self.text_area.text = ""
        self.assertFalse(self.text_area.drawing_text)
        self.assertEqual(self.text_area.text, "")
