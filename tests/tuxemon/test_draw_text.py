# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path

import pytest
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.constants.paths import mods_folder
from tuxemon.platform.const.graphics import FONT_SIZE
from tuxemon.scaling import DefaultScaling
from tuxemon.tools import scale
from tuxemon.ui.text import draw_text
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment
from tuxemon.user_config import CONFIG


@pytest.fixture
def scaling():
    return DefaultScaling(1)


@pytest.fixture
def font():
    font_path = mods_folder / "tuxemon/font" / Path(CONFIG.locale.font_file)
    return Font(font_path.as_posix(), scale(FONT_SIZE))


@pytest.fixture
def font_large():
    font_path = mods_folder / "tuxemon/font" / Path(CONFIG.locale.font_file)
    return Font(font_path.as_posix(), scale(FONT_SIZE + 1))


@pytest.fixture
def rect():
    return Rect(0, 0, 200, 200)


@pytest.fixture
def surface():
    return Surface((400, 300))


def test_draw_text_left(surface, rect, font, scaling):
    background = (0, 0, 0)
    surface.fill(background)

    draw_text(
        surface,
        "Left aligned",
        rect,
        scaling=scaling,
        h_alignment=HorizontalAlignment.LEFT,
        v_alignment=VerticalAlignment.TOP,
        font=font,
        font_color=(255, 255, 255),
    )

    changed = False
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            if surface.get_at((x, y)) != background:
                changed = True
                break
        if changed:
            break

    assert changed, "No pixels changed inside the text region"


def test_draw_text_empty(surface, rect, font, scaling):
    draw_text(
        surface,
        "",
        rect,
        scaling=scaling,
        h_alignment=HorizontalAlignment.LEFT,
        v_alignment=VerticalAlignment.TOP,
        font=font,
        font_color=(0, 0, 0),
    )
    assert surface.get_at((rect.left, rect.top)) == surface.get_at((0, 0))


def test_draw_text_changes_pixels(surface, rect, font, scaling):
    background = (0, 0, 0)
    surface.fill(background)

    draw_text(
        surface, "Hello", rect, scaling, font=font, font_color=(255, 255, 255)
    )

    changed = any(
        surface.get_at((x, y)) != background
        for x in range(rect.left, rect.right)
        for y in range(rect.top, rect.bottom)
    )

    assert changed


def test_draw_text_center_alignment(surface, rect, font, scaling):
    metrics = draw_text(
        surface,
        "Hello",
        rect,
        scaling,
        h_alignment=HorizontalAlignment.CENTER,
        v_alignment=VerticalAlignment.CENTER,
        font=font,
        font_color=(255, 255, 255),
        return_metrics=True,
    )

    assert metrics["rect"].center == rect.center
