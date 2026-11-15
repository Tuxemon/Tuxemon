# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest
from pygame import Surface

from tuxemon.menu.interface import MenuItem


@pytest.fixture
def image():
    return Surface((10, 10))


@pytest.fixture
def game_object():
    return MagicMock()


def test_init_default(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    assert item.label == "Label"
    assert item.description == "Desc"
    assert item.enabled is True
    assert item.in_focus is False
    assert isinstance(item.metadata, dict)


def test_init_custom(image, game_object):
    item = MenuItem(
        image,
        "Label",
        "Desc",
        game_object,
        enabled=False,
        position=(50, 60),
    )
    assert item.enabled is False
    assert item.rect.topleft == (50, 60)


def test_trigger_calls_game_object(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    item.trigger()
    game_object.assert_called_once()


def test_trigger_does_not_call_when_disabled(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object, enabled=False)
    item.trigger()
    game_object.assert_not_called()


def test_enabled_property(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    assert item.enabled is True
    item.enabled = False
    assert item.enabled is False


def test_in_focus_property(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    assert item.in_focus is False
    item.in_focus = True
    assert item.in_focus is True


def test_update_image_runs_without_error(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    item.update_image()  # Should not raise


def test_repr_contains_label_and_enabled(image, game_object):
    item = MenuItem(image, "Label", "Desc", game_object)
    rep = repr(item)
    assert "Label" in rep
    assert "enabled=True" in rep


def test_trigger_ignores_non_callable_non_command(image):
    data_object = {"foo": "bar"}  # no execute(), not callable
    item = MenuItem(image, "Label", "Desc", data_object)
    item.trigger()  # Should not raise


def test_trigger_calls_callable_if_not_command(image):
    fn = MagicMock()
    item = MenuItem(image, "Label", "Desc", fn)

    item.trigger()

    fn.assert_called_once()
