# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest
from pygame import Surface

from tuxemon.monster.sprite import MonsterSpriteHandler


@pytest.fixture
def fake_sheet():
    return Surface((128, 128))


@pytest.fixture
def mock_raw_image(fake_sheet):
    with patch("tuxemon.graphics.load_raw_image", return_value=fake_sheet):
        yield


@pytest.fixture
def handler(mock_raw_image):
    return MonsterSpriteHandler(
        slug="rockitten",
        sheet_path="gfx/sprites/monsters/rockitten_sheet.png",
        front_rect=(0, 0, 64, 64),
        back_rect=(64, 0, 64, 64),
        menu1_rect=(0, 64, 64, 64),
        menu2_rect=(64, 64, 64, 64),
        flairs={},
    )


def test_sheet_loaded_in_constructor(fake_sheet):
    with patch(
        "tuxemon.graphics.load_raw_image", return_value=fake_sheet
    ) as p:
        MonsterSpriteHandler(
            slug="rockitten",
            sheet_path="gfx/sprites/monsters/rockitten_sheet.png",
            front_rect=(0, 0, 64, 64),
            back_rect=(64, 0, 64, 64),
            menu1_rect=(0, 64, 64, 64),
            menu2_rect=(64, 64, 64, 64),
        )
        p.assert_called_once_with("gfx/sprites/monsters/rockitten_sheet.png")


@pytest.mark.parametrize(
    "sprite_type, expected",
    [
        pytest.param("front", (64, 64), id="front_sprite"),
        pytest.param("back", (64, 64), id="back_sprite"),
        pytest.param("menu01", (64, 64), id="menu01_sprite"),
        pytest.param("menu02", (64, 64), id="menu02_sprite"),
    ],
)
def test_slice_sprite(handler, sprite_type, expected):
    sprite = handler.get_sprite(sprite_type, scale=1)
    assert sprite.image.get_size() == expected


def test_sprite_cache(handler):
    s1 = handler.get_sprite("front", scale=1)
    s2 = handler.get_sprite("front", scale=1)
    assert s1.image is s2.image


def test_invalid_sprite_name(handler):
    with pytest.raises(ValueError):
        handler.get_sprite("nope", scale=1)


def test_from_model(fake_sheet):
    model = MagicMock()
    model.slug = "rockitten"
    model.sprites.sheet = "gfx/sprites/monsters/rockitten_sheet.png"
    model.sprites.front_rect = (0, 0, 64, 64)
    model.sprites.back_rect = (64, 0, 64, 64)
    model.sprites.menu1_rect = (0, 64, 64, 64)
    model.sprites.menu2_rect = (64, 64, 64, 64)
    model.sprites.flairs = {}

    with patch("tuxemon.graphics.load_raw_image", return_value=fake_sheet):
        h = MonsterSpriteHandler.from_model(model)

    assert isinstance(h, MonsterSpriteHandler)
    assert h.slug == "rockitten"
