# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from dataclasses import dataclass

import pytest

from tuxemon.db import SoundProperties
from tuxemon.monster.renderer import MonsterRenderer, SoundConfig, SpriteConfig


@dataclass
class DummyMonster:
    slug: str
    sprite_config: SpriteConfig
    sound_config: SoundConfig
    flairs: dict
    flair_slugs: set


class DummyHandler:
    """A fake MonsterSpriteHandler that records calls."""

    def __init__(self, *args, **kwargs):
        self.calls = []

    def load_sprites(self, scale):
        self.calls.append(("load_sprites", scale))

    def get_sprite(self, sprite_type, scale, frame_duration, **kwargs):
        self.calls.append(
            ("get_sprite", sprite_type, scale, frame_duration, kwargs)
        )
        return f"sprite:{sprite_type}"


@pytest.fixture(autouse=True)
def patch_handler(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.monster.renderer.MonsterSpriteHandler", DummyHandler
    )


def test_renderer_initialization():
    monster = DummyMonster(
        slug="testmon",
        sprite_config=SpriteConfig(
            slug="testmon",
            sheet_path="path/to/sheet",
            front_rect=(0, 0, 10, 10),
            back_rect=(0, 0, 10, 10),
            menu1_rect=(0, 0, 10, 10),
            menu2_rect=(0, 0, 10, 10),
            flair_slugs=set(),
        ),
        sound_config=SoundConfig(
            combat=None,
            faint=None,
            default_combat="sound_test_call",
            default_faint="sound_test_faint",
        ),
        flairs={},
        flair_slugs=set(),
    )

    renderer = MonsterRenderer(monster, scale=2.0)

    assert renderer.sprite_handler.calls[0] == ("load_sprites", 2.0)


def test_get_sprite_forwards_kwargs():
    monster = DummyMonster(
        slug="testmon",
        sprite_config=SpriteConfig(
            slug="testmon",
            sheet_path="path/to/sheet",
            front_rect=(0, 0, 10, 10),
            back_rect=(0, 0, 10, 10),
            menu1_rect=(0, 0, 10, 10),
            menu2_rect=(0, 0, 10, 10),
            flair_slugs=set(),
        ),
        sound_config=SoundConfig(
            combat=None,
            faint=None,
            default_combat="sound_test_call",
            default_faint="sound_test_faint",
        ),
        flairs={},
        flair_slugs=set(),
    )

    renderer = MonsterRenderer(monster, scale=1.5)
    sprite = renderer.get_sprite("front", midbottom=(5, 5))

    assert sprite == "sprite:front"

    _, sprite_type, scale, frame_duration, kwargs = (
        renderer.sprite_handler.calls[-1]
    )
    assert sprite_type == "front"
    assert scale == 1.5
    assert kwargs == {"midbottom": (5, 5)}


def test_sound_resolution():
    props = SoundProperties(sfx="sound_confirm", volume=0.8)

    monster = DummyMonster(
        slug="testmon",
        sprite_config=SpriteConfig(
            slug="testmon",
            sheet_path="path/to/sheet",
            front_rect=(0, 0, 10, 10),
            back_rect=(0, 0, 10, 10),
            menu1_rect=(0, 0, 10, 10),
            menu2_rect=(0, 0, 10, 10),
            flair_slugs=set(),
        ),
        sound_config=SoundConfig(
            combat=props,
            faint=None,
            default_combat="sound_default_call",
            default_faint="sound_default_faint",
        ),
        flairs={},
        flair_slugs=set(),
    )

    renderer = MonsterRenderer(monster)

    assert renderer.get_combat_sound() == ("sound_confirm", 0.8)
    assert renderer.get_faint_sound() == ("sound_default_faint", 1.0)
