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
from tuxemon.ui.draw import (
    RenderMode,
    iter_render_text,
)
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
    "text, expected",
    [
        pytest.param(
            "This is a test message",
            "nonempty",
            id="normal",
        ),
        pytest.param(
            "",
            "empty",
            id="empty",
        ),
        pytest.param(
            "This is a short message",
            "nonempty",
            id="short",
        ),
    ],
)
def test_iter_render_text_basic(text, expected, font, rect, scaling):
    renders = list(
        iter_render_text(
            text, font, (0, 0, 0), (255, 255, 255), rect, scaling=scaling
        )
    )
    if expected == "empty":
        assert len(renders) == 0
    else:
        assert len(renders) > 0


def test_iter_render_text_single_word(font, rect, scaling):
    text = "This"
    renders = list(
        iter_render_text(
            text, font, (0, 0, 0), (255, 255, 255), rect, scaling=scaling
        )
    )
    assert len(renders) == len(text)


def test_iter_render_text_trailing_spaces(font, rect, scaling):
    text = "This is a test message "
    r1 = list(
        iter_render_text(
            text, font, (0, 0, 0), (255, 255, 255), rect, scaling=scaling
        )
    )
    r2 = list(
        iter_render_text(
            text.strip(),
            font,
            (0, 0, 0),
            (255, 255, 255),
            rect,
            scaling=scaling,
        )
    )
    assert len(r1) == len(r2)


@pytest.mark.parametrize(
    "alignment",
    [
        pytest.param(HorizontalAlignment.LEFT, id="left"),
        pytest.param(HorizontalAlignment.CENTER, id="center"),
        pytest.param(HorizontalAlignment.RIGHT, id="right"),
    ],
)
def test_iter_render_text_horizontal_alignment(alignment, font, rect, scaling):
    renders = list(
        iter_render_text(
            "Aligned",
            font,
            (0, 0, 0),
            (255, 255, 255),
            rect,
            scaling=scaling,
            h_alignment=alignment,
        )
    )
    assert renders


@pytest.mark.parametrize(
    "alignment",
    [
        pytest.param(VerticalAlignment.TOP, id="top"),
        pytest.param(VerticalAlignment.CENTER, id="center"),
        pytest.param(VerticalAlignment.BOTTOM, id="bottom"),
    ],
)
def test_iter_render_text_vertical_alignment(alignment, font, rect, scaling):
    renders = list(
        iter_render_text(
            "Aligned",
            font,
            (0, 0, 0),
            (255, 255, 255),
            rect,
            scaling=scaling,
            v_alignment=alignment,
        )
    )
    assert renders


def test_iter_render_text_token_spacing(font, rect, scaling):
    text = "Quick brown fox"
    renders = list(
        iter_render_text(
            text,
            font,
            (0, 0, 0),
            (255, 255, 255),
            rect,
            scaling=scaling,
            mode=RenderMode.TOKEN,
        )
    )

    for prev, curr in zip(renders, renders[1:]):
        assert curr.rect.left >= prev.rect.right

    assert " ".join(r.char for r in renders) == text
