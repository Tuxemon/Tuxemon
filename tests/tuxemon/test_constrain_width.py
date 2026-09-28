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
from tuxemon.ui.draw import constrain_width
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
    "text, width, expected",
    [
        pytest.param("", 200, 1, id="empty"),
        pytest.param("This", 200, 1, id="single_word"),
    ],
)
def test_constrain_width_basic(text, width, expected, font):
    lines = list(constrain_width(text, font, width))
    assert len(lines) == expected


def test_constrain_width_multiple_lines(font):
    text = "This is a test message that is too long for the width"
    lines = list(constrain_width(text, font, 100))
    assert len(lines) >= 2


def test_strict_mode_true(font):
    text = "a" * 100
    with pytest.raises(RuntimeError):
        list(constrain_width(text, font, 10))


def test_strict_mode_false(font):
    text = "a" * 100
    lines = list(constrain_width(text, font, 10, strict_mode=False))
    assert lines == [text]


def test_font_large_more_wraps(font, font_large):
    text = "This is a test message that is too long for the width"
    small = list(constrain_width(text, font, 200))
    large = list(constrain_width(text, font_large, 200))
    assert len(large) >= len(small)
