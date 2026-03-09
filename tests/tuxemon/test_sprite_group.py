# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

from pygame import Rect

from tuxemon.sprite import SpriteGroup


def test_calc_bounding_rect_empty_group_returns_zero_rect() -> None:
    group = SpriteGroup()

    assert group.calc_bounding_rect() == Rect(0, 0, 0, 0)
