# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from unittest.mock import Mock

import pytest
from pygame.font import Font
from pygame.rect import Rect

from tuxemon.constants.paths import mods_folder
from tuxemon.platform.const.graphics import FONT_SIZE
from tuxemon.tools import scale
from tuxemon.ui.draw import OverflowHandler, RenderedChar, TextOverflow
from tuxemon.ui.text_renderer import TextRenderer
from tuxemon.user_config import CONFIG

FONT_PATH = mods_folder / "tuxemon/font" / Path(CONFIG.locale.font_file)


@pytest.fixture
def font():
    return Font(FONT_PATH.as_posix(), scale(FONT_SIZE))


@pytest.fixture
def rect():
    return Rect(0, 0, 100, 100)


@pytest.fixture
def renderer():
    return Mock(spec=TextRenderer)


@pytest.fixture
def handler(font, rect):
    return OverflowHandler(font, rect, TextOverflow.ELLIPSIS)


def test_init(handler, font, rect):
    assert handler.font == font
    assert handler.rect == rect
    assert handler.behavior == TextOverflow.ELLIPSIS
    assert handler.ellipsis == "…"
    assert handler.ellipsis_width == scale(FONT_SIZE)


def test_get_ellipsis_char(handler, renderer):
    top = 10
    fg = (255, 255, 255)
    bg = (0, 0, 0)

    surface = Mock()
    surface.get_rect.return_value.top = top
    renderer.shadow_text.return_value = surface

    rendered = handler.get_ellipsis_char(top, fg, bg, renderer)

    assert isinstance(rendered, RenderedChar)
    assert rendered.rect.top == top
    renderer.shadow_text.assert_called_once_with("…", bg=bg, fg=fg)


def test_handle_render_attempt_expand(font, rect, renderer):
    handler = OverflowHandler(font, rect, TextOverflow.EXPAND)

    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=50,
        segment_width=20,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is True
    assert ellipsis is None


def test_handle_render_attempt_fits(handler, renderer):
    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=50,
        segment_width=20,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is True
    assert ellipsis is None


def test_handle_render_attempt_does_not_fit_ellipsis(handler, renderer, rect):
    current_x = rect.right - handler.ellipsis_width
    surface = Mock()
    surface.get_rect.return_value.top = 10
    renderer.shadow_text.return_value = surface

    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=current_x,
        segment_width=30,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is False
    assert ellipsis is not None


def test_handle_render_attempt_does_not_fit_no_ellipsis(handler, renderer):
    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=120,
        segment_width=20,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is False
    assert ellipsis is None


def test_handle_render_attempt_ellipsis_fits(handler, renderer, rect):
    current_x = rect.right - handler.ellipsis_width - 5

    surface = Mock()
    surface.get_rect.return_value.top = 10
    renderer.shadow_text.return_value = surface

    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=current_x,
        segment_width=50,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is False
    assert ellipsis is not None


def test_handle_render_attempt_clip(font, rect, renderer):
    handler = OverflowHandler(font, rect, TextOverflow.CLIP)

    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=120,
        segment_width=20,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is False
    assert ellipsis is None


def test_ellipsis_exact_fit(handler, renderer, rect):
    current_x = rect.right - handler.ellipsis_width

    surface = Mock()
    surface.get_rect.return_value.top = 10
    renderer.shadow_text.return_value = surface

    should_render, ellipsis = handler.handle_render_attempt(
        current_x_position=current_x,
        segment_width=50,
        top=10,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
        renderer=renderer,
    )

    assert should_render is False
    assert ellipsis is not None
