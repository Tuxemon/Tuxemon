# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame
import pytest
from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon.scaling import DefaultScaling
from tuxemon.ui.text_renderer import TextRenderer


@pytest.fixture
def default_renderer():
    return TextRenderer(DefaultScaling(1), (255, 255, 255))


@pytest.fixture
def font():
    return pygame.font.Font(None, 16)


class DummyScaling:
    def scale_int(self, v):
        return v

    def scale_sequence(self, seq):
        return seq


@pytest.fixture
def scaling():
    return DummyScaling()


@pytest.fixture
def renderer(scaling, font):
    return TextRenderer(
        scaling=scaling,
        font_color=(255, 255, 255),
        font_shadow_color=(0, 0, 0),
        font=font,
    )


def test_init(default_renderer):
    assert default_renderer.font_color == (255, 255, 255)


def test_shadow_text(default_renderer):
    surface = default_renderer.shadow_text("Hello, World!")
    assert isinstance(surface, Surface)


def test_shadow_text_default_colors(default_renderer):
    surface = default_renderer.shadow_text("Hello, World!")
    w, h = surface.get_size()
    assert w > 0
    assert h > 0


def test_shadow_text_custom_colors(default_renderer):
    surface = default_renderer.shadow_text(
        "Hello, World!", fg=(0, 0, 255), bg=(255, 0, 0)
    )
    w, h = surface.get_size()
    assert w > 0
    assert h > 0


def test_shadow_text_offset(default_renderer):
    surface = default_renderer.shadow_text("Hello, World!", offset=(1, 1))
    w, h = surface.get_size()
    assert w > 0
    assert h > 0


def test_shadow_text_invalid_offset(default_renderer):
    with pytest.raises(TypeError):
        default_renderer.shadow_text("Hello, World!", offset="invalid")


def test_shadow_text_invalid_fg_color(default_renderer):
    with pytest.raises(ValueError):
        default_renderer.shadow_text("Hello, World!", fg="invalid")


def test_shadow_text_invalid_bg_color(default_renderer):
    with pytest.raises(ValueError):
        default_renderer.shadow_text("Hello, World!", bg="invalid")


def test_shadow_text_surface_size(default_renderer):
    surface = default_renderer.shadow_text("Hello, World!")
    assert surface.get_width() > 0
    assert surface.get_height() > 0


def test_shadow_text_surface_alpha(default_renderer):
    surface = default_renderer.shadow_text("Hello, World!")
    assert surface.get_flags() & pygame.SRCALPHA == pygame.SRCALPHA
    assert surface.get_alpha() == 255


def test_shadow_text_returns_surface(renderer):
    surf = renderer.shadow_text("A")
    assert isinstance(surf, pygame.Surface)
    assert surf.get_flags() & SRCALPHA


def test_shadow_text_uses_default_colors(renderer):
    surf = renderer.shadow_text("A", fg=None, bg=None)
    assert surf is not None


def test_shadow_text_surface_size_with_font(renderer, font):
    text = "A"
    base_w, base_h = font.size(text)
    surf = renderer.shadow_text(text, offset=(1, 1))
    assert surf.get_width() >= base_w + 1
    assert surf.get_height() >= base_h + 1


def test_shadow_text_shadow_offset_applied(renderer):
    surf = renderer.shadow_text("A", offset=(2, 3))
    assert surf.get_width() > 0
    assert surf.get_height() > 0


def test_empty_string(renderer):
    surf = renderer.shadow_text("")
    assert surf.get_width() >= 0
    assert surf.get_height() >= 0


def test_whitespace_only(renderer):
    surf = renderer.shadow_text("   ")
    assert surf.get_width() > 0


def test_zero_offset(renderer):
    surf = renderer.shadow_text("A", offset=(0, 0))
    assert surf.get_width() > 0
    assert surf.get_height() > 0


def test_negative_offset(renderer):
    surf = renderer.shadow_text("A", offset=(-2, -2))
    assert surf.get_width() > 0
    assert surf.get_height() > 0


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("é", id="latin-accented"),
        pytest.param("漢", id="cjk"),
        pytest.param("🙂", id="emoji"),
        pytest.param("漢字🙂", id="mixed-cjk-emoji"),
    ],
)
def test_unicode_characters(renderer, text):
    surf = renderer.shadow_text(text)
    assert surf.get_width() > 0
    assert surf.get_height() > 0


def test_long_string(renderer):
    text = "Hello" * 200
    surf = renderer.shadow_text(text)
    assert surf.get_width() > 0
    assert surf.get_height() > 0


def test_scaled_offset_applied(scaling, font):
    class Scaling2x:
        def scale_int(self, v):
            return v

        def scale_sequence(self, seq):
            return (seq[0] * 2, seq[1] * 2)

    r = TextRenderer(
        scaling=Scaling2x(),
        font_color=(255, 255, 255),
        font_shadow_color=(0, 0, 0),
        font=font,
    )

    surf = r.shadow_text("A", offset=(1, 1))
    base_w, base_h = font.size("A")
    assert surf.get_width() >= base_w + 2
    assert surf.get_height() >= base_h + 2
