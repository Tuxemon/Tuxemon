# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from pygame.rect import Rect

from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment

logger = logging.getLogger(__name__)


class CombatZone:
    def __init__(self, screen_rect: Rect, margin: int = 20):
        """
        Classifies Rects into horizontal and vertical zones based on screen layout.

        Parameters:
            screen_rect: The full screen area as a Rect.
            margin: Padding margin for determining center zone tolerance.
        """
        self.screen_rect = screen_rect
        self.margin = margin
        self.mid_x = screen_rect.centerx
        self.mid_y = screen_rect.centery

    def get_zone(
        self, rect: Rect
    ) -> tuple[VerticalAlignment, HorizontalAlignment]:
        x, y = rect.centerx, rect.centery

        # Horizontal
        if x < self.mid_x - self.margin:
            h_zone = HorizontalAlignment.LEFT
        elif x > self.mid_x + self.margin:
            h_zone = HorizontalAlignment.RIGHT
        else:
            h_zone = HorizontalAlignment.CENTER

        # Vertical
        if y < self.mid_y - self.margin:
            v_zone = VerticalAlignment.TOP
        elif y > self.mid_y + self.margin:
            v_zone = VerticalAlignment.BOTTOM
        else:
            v_zone = VerticalAlignment.CENTER

        return v_zone, h_zone

    def get_horizontal_offset(
        self, rect: Rect, distance: int = 150, center: int = 0
    ) -> int:
        """
        Returns a horizontal offset based on the rect's classified horizontal
        alignment.

        Positive means move right, negative means left, zero for center.
        """
        _, h_align = self.get_zone(rect)
        if h_align == HorizontalAlignment.LEFT:
            return +distance
        elif h_align == HorizontalAlignment.RIGHT:
            return -distance
        return center  # CENTER

    def get_vertical_offset(
        self, rect: Rect, distance: int = 150, center: int = 0
    ) -> int:
        """
        Returns a vertical offset based on the rect's classified vertical
        alignment.

        Positive means move down, negative means up, zero for center.
        """
        v_align, _ = self.get_zone(rect)
        if v_align == VerticalAlignment.TOP:
            return -distance
        elif v_align == VerticalAlignment.BOTTOM:
            return +distance
        return center  # CENTER
