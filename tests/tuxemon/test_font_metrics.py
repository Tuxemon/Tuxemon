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
from tuxemon.ui.draw import get_font_height, get_text_size
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


def test_get_font_height_positive(font):
    assert get_font_height(font) > 0


def test_get_font_height_matches_text_size(font):
    h = get_font_height(font)
    _, h2 = get_text_size("Tg", font)
    assert h == h2


def test_get_text_size(font):
    w, h = get_text_size("Test", font)
    assert w > 0 and h > 0
