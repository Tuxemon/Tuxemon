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
from tuxemon.ui.draw import calculate_alignment_offset
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


@pytest.mark.parametrize(
    "h, v, expected",
    [
        pytest.param(
            HorizontalAlignment.LEFT,
            VerticalAlignment.TOP,
            (0, 0),
            id="left_top",
        ),
        pytest.param(
            HorizontalAlignment.CENTER,
            VerticalAlignment.CENTER,
            (25, 25),
            id="center_center",
        ),
        pytest.param(
            HorizontalAlignment.RIGHT,
            VerticalAlignment.BOTTOM,
            (50, 50),
            id="right_bottom",
        ),
    ],
)
def test_alignment_offset(h, v, expected):
    rect = Rect(0, 0, 100, 100)
    assert calculate_alignment_offset(rect, 50, 50, h, v) == expected


def test_negative_content():
    rect = Rect(0, 0, 100, 100)
    with pytest.raises(ValueError):
        calculate_alignment_offset(
            rect,
            -50,
            -50,
            HorizontalAlignment.CENTER,
            VerticalAlignment.CENTER,
        )
