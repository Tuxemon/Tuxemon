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
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    assert menu_item.label == "Test Label"
    assert menu_item.description == "Test Description"
    assert menu_item.enabled is True


def test_init_custom(image, game_object):
    menu_item = MenuItem(
        image,
        "Test Label",
        "Test Description",
        game_object,
        enabled=False,
        position=(100, 100),
    )
    assert menu_item.label == "Test Label"
    assert menu_item.description == "Test Description"
    assert menu_item.enabled is False


def test_update_image_focus(image, game_object):
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    menu_item._in_focus = True
    menu_item.update_image = MagicMock()
    menu_item.update_image()
    menu_item.update_image.assert_called_once()


def test_update_image_enabled(image, game_object):
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    menu_item.enabled = False
    menu_item.update_image = MagicMock()
    menu_item.update_image()
    menu_item.update_image.assert_called_once()


def test_enabled_property(image, game_object):
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    assert menu_item.enabled is True
    menu_item.enabled = False
    assert menu_item.enabled is False


def test_in_focus_property(image, game_object):
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    assert menu_item.in_focus is False
    menu_item.in_focus = True
    assert menu_item.in_focus is True


def test_repr(image, game_object):
    menu_item = MenuItem(image, "Test Label", "Test Description", game_object)
    rep = str(menu_item)
    assert "Test Label" in rep
    assert "enabled=True" in rep
