# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from pygame.rect import Rect

from tuxemon.ui.dialogue import calc_dialog_rect, resolve_reference_rect
from tuxemon.ui.text_alignment import DialogPosition


class TestCalcDialogRect(unittest.TestCase):

    def setUp(self):
        self.screen_rect = Rect(0, 0, 800, 600)

    def test_resolve_reference_rect_screen(self):
        target_coords = None
        reference_rect = resolve_reference_rect(
            self.screen_rect, target_coords
        )
        self.assertEqual(reference_rect, self.screen_rect)

    def test_resolve_reference_rect_rect(self):
        target_coords = Rect(100, 100, 200, 200)
        reference_rect = resolve_reference_rect(
            self.screen_rect, target_coords
        )
        self.assertEqual(reference_rect, target_coords)

    def test_resolve_reference_rect_coords(self):
        target_coords = (100, 100)
        reference_rect = resolve_reference_rect(
            self.screen_rect, target_coords
        )
        self.assertEqual(reference_rect, Rect(100, 100, 1, 1))

    def test_calc_dialog_rect_top(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.TOP)
        self.assertEqual(rect.top, self.screen_rect.top)
        self.assertEqual(rect.centerx, self.screen_rect.centerx)

    def test_calc_dialog_rect_bottom(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.BOTTOM)
        self.assertEqual(rect.bottom, self.screen_rect.bottom)
        self.assertEqual(rect.centerx, self.screen_rect.centerx)

    def test_calc_dialog_rect_center(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.CENTER)
        self.assertEqual(rect.center, self.screen_rect.center)

    def test_calc_dialog_rect_topleft(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.TOPLEFT)
        self.assertEqual(rect.topleft, self.screen_rect.topleft)

    def test_calc_dialog_rect_topright(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.TOPRIGHT)
        self.assertEqual(rect.topright, self.screen_rect.topright)

    def test_calc_dialog_rect_bottomleft(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.BOTTOMLEFT)
        self.assertEqual(rect.bottomleft, self.screen_rect.bottomleft)

    def test_calc_dialog_rect_bottomright(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.BOTTOMRIGHT)
        self.assertEqual(rect.bottomright, self.screen_rect.bottomright)

    def test_calc_dialog_rect_left(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.LEFT)
        self.assertEqual(rect.left, self.screen_rect.left)
        self.assertEqual(rect.centery, self.screen_rect.centery)

    def test_calc_dialog_rect_right(self):
        rect = calc_dialog_rect(self.screen_rect, DialogPosition.RIGHT)
        self.assertEqual(rect.right, self.screen_rect.right)
        self.assertEqual(rect.centery, self.screen_rect.centery)

    def test_calc_dialog_rect_at_target(self):
        target_coords = (100, 100)
        rect = calc_dialog_rect(
            self.screen_rect, DialogPosition.AT_TARGET, target_coords
        )
        self.assertEqual(rect.topleft, target_coords)

    def test_calc_dialog_rect_at_target_invalid(self):
        target_coords = Rect(100, 100, 200, 200)
        with self.assertRaises(ValueError):
            calc_dialog_rect(
                self.screen_rect, DialogPosition.AT_TARGET, target_coords
            )

    def test_calc_dialog_rect_invalid_position(self):
        with self.assertRaises(ValueError):
            calc_dialog_rect(self.screen_rect, "invalid_position")
