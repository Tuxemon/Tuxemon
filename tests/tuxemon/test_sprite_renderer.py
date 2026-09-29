# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pygame
import pytest

import tuxemon.user_config
from tuxemon.config import PlayerConfig, TuxemonConfig
from tuxemon.map.view import EntityFacing, SpriteRenderer
from tuxemon.prepare import DISPLAY_CONTEXT
from tuxemon.user_config import CONFIG

pygame.display.init()


def make_frame(w=16, h=32):
    return pygame.Surface((w, h))


def fake_sheet(rows=4, cols=3, w=16, h=32):
    return [make_frame(w, h) for _ in range(rows * cols)]


def test_load_static_prop(monkeypatch):
    npc = Mock()
    npc.template = Mock(
        is_static_prop=True,
        sprite_name="sign",
        frame_divisor=3,
        speed_factor=1.0,
        animation_speed=1.0,
    )
    npc.moverate = 1.0
    npc.tile_pos = (100, 200)

    fake_surface = make_frame(32, 32)

    monkeypatch.setattr(
        "tuxemon.map.view.load_and_scale_with_cache",
        lambda p: fake_surface,
    )

    renderer = SpriteRenderer(npc)
    renderer.load_sprites(npc.template)

    assert renderer.standing[EntityFacing.front] is fake_surface
    assert renderer.sprite == {}  # no animations


def test_load_from_sheet(monkeypatch):
    npc = Mock()
    npc.template = Mock(
        is_static_prop=False,
        sprite_name="hero",
        frame_width=16,
        frame_height=32,
        rows=4,
        columns=3,
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )
    npc.moverate = 1.0
    npc.tile_pos = (0, 0)

    monkeypatch.setattr(
        "tuxemon.map.view.slice_spritesheet_surface",
        lambda *args, **kwargs: fake_sheet(),
    )

    renderer = SpriteRenderer(npc)
    renderer.load_sprites(npc.template)

    assert len(renderer.standing) == 4

    assert "front" in renderer.sprite
    assert "left" in renderer.sprite
    assert "right" in renderer.sprite
    assert "back" in renderer.sprite

    assert "front_walk" in renderer.sprite
    assert "left_walk" in renderer.sprite
    assert "right_walk" in renderer.sprite
    assert "back_walk" in renderer.sprite


def test_walking_animation_pattern(monkeypatch):
    npc = Mock()
    npc.template = Mock(
        is_static_prop=False,
        sprite_name="hero",
        frame_width=16,
        frame_height=32,
        rows=4,
        columns=3,
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )
    npc.moverate = 1.0
    npc.tile_pos = (0, 0)

    frames = fake_sheet()
    monkeypatch.setattr(
        "tuxemon.map.view.slice_spritesheet_surface",
        lambda *args, **kwargs: frames,
    )

    renderer = SpriteRenderer(npc)
    renderer.load_sprites(npc.template)

    walk = renderer.sprite["front_walk"]
    images = walk._frame_manager.images

    assert images[0] is frames[1]
    assert images[1] is frames[0]
    assert images[2] is frames[1]
    assert images[3] is frames[2]


def test_tall_sprite_offset(monkeypatch):
    npc = Mock()
    npc.template = Mock(
        is_static_prop=False,
        sprite_name="hero",
        frame_width=16,
        frame_height=64,
        rows=4,
        columns=3,
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )
    npc.moverate = 1.0
    npc.tile_pos = (100, 200)

    # Real pygame surfaces
    frames = [pygame.Surface((16, 64)) for _ in range(12)]

    monkeypatch.setattr(
        "tuxemon.map.view.slice_spritesheet_surface",
        lambda *args, **kwargs: frames,
    )

    fake = TuxemonConfig(config_path=None)
    fake.config_model.player = PlayerConfig(player_walkrate=1.0)

    monkeypatch.setattr(tuxemon.user_config, "CONFIG", fake)
    renderer = SpriteRenderer(npc)
    renderer.load_sprites(npc.template)

    expected_offset = 64 - DISPLAY_CONTEXT.tile_size[1]
    assert renderer.rect.y == 200 - expected_offset


def test_frame_duration():
    template = Mock(
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )

    npc = Mock(template=template, moverate=1.0)

    renderer = SpriteRenderer(npc)
    duration = renderer.frame_duration

    expected = (1000 / 1.0) / 3 / 1000 * 2.0 * 1.0
    assert duration == expected


def test_get_animation_frame_updates_rate(monkeypatch):
    fake = TuxemonConfig(config_path=None)
    fake.config_model.player = PlayerConfig(player_walkrate=1.0)

    monkeypatch.setattr(tuxemon.user_config, "CONFIG", fake)

    npc = Mock(moverate=2.0)
    npc.template = Mock(
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )

    renderer = SpriteRenderer(npc)

    anim = Mock()
    anim.get_current_frame.return_value = "FRAME"

    renderer.sprite = {"front_walk": anim}

    frame = renderer.get_animation_frame("front_walk", renderer.sprite, npc)

    assert anim.rate == npc.moverate / CONFIG.player_walkrate
    assert frame == "FRAME"


def test_missing_animation_raises(monkeypatch):
    fake = TuxemonConfig(config_path=None)
    fake.config_model.player = PlayerConfig(player_walkrate=1.0)
    monkeypatch.setattr(tuxemon.user_config, "CONFIG", fake)
    npc = Mock(moverate=1.0)
    npc.template = Mock(
        frame_divisor=3,
        speed_factor=2.0,
        animation_speed=1.0,
    )

    renderer = SpriteRenderer(npc)

    with pytest.raises(ValueError):
        renderer.get_animation_frame("does_not_exist", {}, npc)
