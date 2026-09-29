# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from pygame import SRCALPHA
from pygame.color import Color
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.scaling import DefaultScaling
from tuxemon.ui.draw import TextOverflow, iter_render_text
from tuxemon.ui.text import TextArea
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment


class DummyChar:
    def __init__(self, ch="X"):
        self.surface = Surface((1, 1))
        self.rect = self.surface.get_rect()


def dummy_iter_render_text(**kwargs):
    for _ in kwargs["text"]:
        yield DummyChar()


@pytest.fixture
def font():
    return Font(None, 16)


@pytest.fixture
def rect():
    return Rect(0, 0, 100, 40)


@pytest.fixture
def text_area(font, rect):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=rect,
        scaling=DefaultScaling(1),
    )
    ta._iter = None
    return ta


@pytest.fixture
def small_rect():
    return Rect(0, 0, 100, 20)


@pytest.fixture
def stress_text_area(font, small_rect):
    return TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=small_rect,
        scaling=DefaultScaling(1),
    )


def test_initial_state(text_area):
    assert text_area.text == ""
    assert text_area.drawing_text is False


def test_text_setter_triggers_animation(font):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 200, 50),
        scaling=DefaultScaling(1),
    )
    ta._start_text_animation = lambda: setattr(ta, "drawing_text", True)
    ta.text = "Hello"
    assert ta.text == "Hello"
    assert ta.drawing_text is True


def test_len_returns_length(text_area):
    text_area.text = "abc"
    assert len(text_area) == 3


def test_iter_and_next(text_area):
    text_area._iter = iter([DummyChar(), DummyChar()])
    text_area.animated = True
    text_area.drawing_text = True
    next(text_area)
    assert text_area.drawing_text is True
    with pytest.raises(StopIteration):
        while True:
            next(text_area)
    assert text_area.drawing_text is False


def test_non_animated_text_sets_image_directly(text_area):
    text_area.animated = False
    text_area.text = "Direct"
    assert text_area.image is not None


def test_overflow_behavior_setter(text_area):
    text_area.set_overflow_behavior(TextOverflow.WRAP)
    assert text_area.overflow_behavior == TextOverflow.WRAP


def test_start_text_animation_resets_surface(font):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 10, 10),
        scaling=DefaultScaling(1),
    )

    global iter_render_text
    old_iter = iter_render_text
    iter_render_text = dummy_iter_render_text
    try:
        ta.text = "abc"
        assert ta.drawing_text is True
        assert ta._iter is not None
    finally:
        iter_render_text = old_iter


def test_next_raises_stopiteration_when_not_animated(text_area):
    text_area.animated = False
    with pytest.raises(StopIteration):
        next(text_area)


def test_text_setter_same_value_restarts_animation(text_area):
    text_area.text = "abc"
    text_area.drawing_text = False
    text_area.text = "abc"
    assert text_area.drawing_text is True


def test_empty_string(stress_text_area):
    stress_text_area.text = ""
    assert stress_text_area.drawing_text is False
    assert stress_text_area.text == ""


def test_repeated_text_changes(stress_text_area):
    for msg in ["One", "Two", "Three"]:
        stress_text_area.text = msg
        for _ in stress_text_area:
            pass
        assert stress_text_area.text == msg
        assert stress_text_area.drawing_text is False


def test_drawing_text_stays_true_until_stopiteration(stress_text_area):
    stress_text_area.text = "Hello"
    assert stress_text_area.drawing_text is True

    count = 0
    try:
        while True:
            next(stress_text_area)
            count += 1
            assert stress_text_area.drawing_text is True
    except StopIteration:
        pass

    assert count == len(stress_text_area.text)
    assert stress_text_area.drawing_text is False


def test_non_animated_text_is_fully_rendered_immediately(stress_text_area):
    stress_text_area.animated = False
    stress_text_area.text = "Static Text"
    assert stress_text_area.text == "Static Text"
    assert stress_text_area.drawing_text is False


def test_len_after_setting_empty_text(stress_text_area):
    stress_text_area.text = "A B C"
    assert len(stress_text_area) == 5
    stress_text_area.text = ""
    assert len(stress_text_area) == 0


def test_next_on_completed_text_raises_stopiteration(stress_text_area):
    stress_text_area.animated = True
    stress_text_area.drawing_text = False

    with pytest.raises(StopIteration):
        next(stress_text_area)


def test_empty_string_animation_state(stress_text_area):
    stress_text_area.animated = True
    stress_text_area.text = "Testing"
    assert stress_text_area.drawing_text is True

    stress_text_area.text = ""
    assert stress_text_area.drawing_text is False
    assert stress_text_area.text == ""


def test_background_and_diagnostics_integration(font, rect):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=rect,
        scaling=DefaultScaling(1),
        debug_rendering=True,
    )
    ta.text = "Hi"
    px = ta.image.get_at((0, 0))
    assert px.a > 0


def test_static_rendering_draws_text(text_area):
    text_area.animated = False
    text_area.text = "Hello"

    nonzero = False
    for x in range(text_area.image.get_width()):
        for y in range(text_area.image.get_height()):
            if text_area.image.get_at((x, y)).a > 0:
                nonzero = True
                break
        if nonzero:
            break

    assert nonzero, "Static text should be drawn immediately"


def test_animation_iterates_one_char_per_symbol(text_area):
    text_area.text = "ABC"

    count = 0
    try:
        while True:
            next(text_area)
            count += 1
    except StopIteration:
        pass

    assert count == 3


def test_overflow_behavior_passed_to_iter(text_area, monkeypatch):
    captured = {}

    def fake_iter_render_text(**kwargs):
        captured.update(kwargs)
        return iter([])

    monkeypatch.setattr(
        "tuxemon.ui.text.iter_render_text", fake_iter_render_text
    )

    text_area.set_overflow_behavior(TextOverflow.WRAP)
    text_area.text = "Hello"

    assert captured["overflow_behavior"] == TextOverflow.WRAP


def test_alignment_parameters_passed(font, monkeypatch):
    captured = {}

    def fake_iter_render_text(**kwargs):
        captured.update(kwargs)
        return iter([])

    monkeypatch.setattr(
        "tuxemon.ui.text.iter_render_text", fake_iter_render_text
    )

    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 100, 40),
        scaling=DefaultScaling(1),
        h_alignment=HorizontalAlignment.CENTER,
        v_alignment=VerticalAlignment.BOTTOM,
    )
    ta.text = "Hello"

    assert captured["h_alignment"] == HorizontalAlignment.CENTER
    assert captured["v_alignment"] == VerticalAlignment.BOTTOM


def test_image_initialized_in_constructor(text_area):
    assert hasattr(text_area, "image")
    assert isinstance(text_area.image, Surface)


def test_static_text_does_not_use_background(font):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 100, 30),
        scaling=DefaultScaling(1),
        background_color=(255, 0, 0),
    )
    ta.animated = False
    ta.text = "Hello"
    px = ta.image.get_at((0, 0))
    assert px == Color(255, 0, 0)


def test_animated_text_uses_background(font):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 100, 30),
        scaling=DefaultScaling(1),
        background_color=(0, 255, 0),
    )
    ta.text = "Hi"
    px = ta.image.get_at((0, 0))
    assert px == Color(0, 255, 0)


def test_iter_returns_self(text_area):
    assert iter(text_area) is text_area


def test_empty_text_resets_image(font):
    ta = TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 50, 20),
        scaling=DefaultScaling(1),
    )
    ta.image = Surface((50, 20), SRCALPHA)
    ta.text = ""
    assert ta.image.get_size() == (50, 20)
    px = ta.image.get_at((0, 0))
    assert px.a == 0
