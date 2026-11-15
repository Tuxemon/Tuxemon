# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

from tuxemon.state.animation_mixin import AnimationMixin


class Dummy(AnimationMixin):
    """A simple concrete class to test the mixin."""

    def __init__(self):
        super().__init__()


def test_init_creates_animation_group(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()
    assert d.anim is mock_group
    assert d._scheduled_task is None


def test_animate_calls_animation_group(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()
    d.animate("target", x=10)

    mock_group.animate.assert_called_once_with("target", x=10)


def test_task_calls_animation_group(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()
    d.task(lambda: None, interval=1.0)
    mock_group.task.assert_called_once()


def test_chain_animations(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()

    def fn():
        return None

    d.chain_animations(fn, start_delay=0.5)
    mock_group.chain_animations.assert_called_once_with(fn, start_delay=0.5)


def test_remove_animations_of(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()
    d.remove_animations_of("obj")
    mock_group.remove_of.assert_called_once_with("obj")


def test_update_animations(monkeypatch):
    mock_group = MagicMock()
    monkeypatch.setattr(
        "tuxemon.state.animation_mixin.AnimationGroup", lambda: mock_group
    )
    d = Dummy()
    d.update_animations(0.16)
    mock_group.update.assert_called_once_with(0.16)
