# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from pygame.surface import Surface

from tuxemon.scaling import DefaultScaling
from tuxemon.ui.text import MultilineTextRenderer
from tuxemon.ui.text_renderer import TextRenderer


@pytest.fixture
def text_renderer():
    return TextRenderer(DefaultScaling(1), (255, 255, 255))


@pytest.fixture
def multiline(text_renderer):
    return MultilineTextRenderer(text_renderer)


def test_init(multiline, text_renderer):
    assert multiline.text_renderer == text_renderer
    assert multiline.line_spacing == 0


def test_render_lines_single_line(multiline):
    lines = multiline.render_lines("Hello, World!", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 1
    assert isinstance(lines[0][0], Surface)


def test_render_lines_multiple_lines(multiline):
    lines = multiline.render_lines("Hello, World! This is a test.", 10)
    assert isinstance(lines, list)
    assert len(lines) > 1
    for surf, _ in lines:
        assert isinstance(surf, Surface)


def test_render_lines_max_width(multiline):
    lines = multiline.render_lines("Hello, World! This is a test.", 20)
    assert isinstance(lines, list)
    assert len(lines) > 1
    for surf, _ in lines:
        assert isinstance(surf, Surface)


def test_render_lines_line_spacing(text_renderer):
    ml = MultilineTextRenderer(text_renderer, line_spacing=10)
    lines = ml.render_lines("Hello, World! This is a test.", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 1
    assert isinstance(lines[0][0], Surface)


def test_render_lines_single_character(multiline):
    lines = multiline.render_lines("a", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 1
    assert isinstance(lines[0][0], Surface)


def test_render_lines_non_ascii_characters(multiline):
    lines = multiline.render_lines("éàü", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 1
    assert isinstance(lines[0][0], Surface)


def test_render_lines_surface_size(multiline):
    lines = multiline.render_lines("Hello, World!", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 1
    surf, height = lines[0]
    assert surf.get_width() > 0
    assert height > 0


def test_render_lines_empty_string(multiline):
    lines = multiline.render_lines("", 1000)
    assert isinstance(lines, list)
    assert len(lines) == 0


def test_render_lines_long_string(multiline):
    lines = multiline.render_lines("a" * 1000, 1000)
    assert isinstance(lines, list)
    assert len(lines) > 0


def test_render_lines_newline(multiline):
    lines = multiline.render_lines("Hello, World!\nThis is a test.", 1000)
    assert isinstance(lines, list)
    assert len(lines) > 1
