# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from tuxemon.db import SoundProperties
from tuxemon.monster.sprite import (
    Flair,
    FlairApplier,
    MonsterSpriteHandler,
    SpriteLoader,
)
from tuxemon.sprite import Sprite

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)

from dataclasses import dataclass


@dataclass
class SoundConfig:
    combat: SoundProperties | None
    faint: SoundProperties | None
    default_combat: str
    default_faint: str


@dataclass
class SpriteConfig:
    slug: str
    sheet_path: str
    front_rect: tuple[int, int, int, int]
    back_rect: tuple[int, int, int, int]
    menu1_rect: tuple[int, int, int, int]
    menu2_rect: tuple[int, int, int, int]
    flair_slugs: set[str]


class MonsterRenderer:
    """
    Handles all rendering concerns for a Monster.
    Loads sprites, applies scaling, and returns Sprite objects.
    """

    def __init__(
        self,
        monster: Monster,
        scale: float | None = None,
        frame_duration: float | None = None,
    ):
        self.monster = monster
        self.scale = scale or 1.0
        self.frame_duration = frame_duration or 0.25
        self.sprite_handler = self._setup_handler()

    def _resolve_flairs(self) -> dict[str, Flair]:
        """Return the monster's saved flairs or generate new ones from slugs."""
        if self.monster.flairs:
            return self.monster.flairs

        return FlairApplier.create(self.monster.flair_slugs)

    def _setup_handler(self) -> MonsterSpriteHandler:
        """Initialize and load the monster's sprite handler."""
        cfg = self.monster.sprite_config
        loader = SpriteLoader()

        handler = MonsterSpriteHandler(
            slug=cfg.slug,
            sheet_path=loader.resolve_path(cfg.sheet_path),
            front_rect=cfg.front_rect,
            back_rect=cfg.back_rect,
            menu1_rect=cfg.menu1_rect,
            menu2_rect=cfg.menu2_rect,
            flairs=FlairApplier.create(cfg.flair_slugs),
        )

        handler.load_sprites(self.scale)
        return handler

    def get_sprite(self, sprite_type: str = "front", **kwargs: Any) -> Sprite:
        """Return a rendered sprite of the specified type."""
        return self.sprite_handler.get_sprite(
            sprite_type=sprite_type,
            scale=self.scale,
            frame_duration=self.frame_duration,
            **kwargs,
        )

    def get_combat_sound(self) -> tuple[str, float]:
        """Return the monster's combat sound effect and volume."""
        cfg = self.monster.sound_config
        call = cfg.combat

        if isinstance(call, SoundProperties):
            sfx = call.sfx if call.sfx is not None else cfg.default_combat
            volume = float(call.volume)
            return sfx, volume

        return cfg.default_combat, 1.0

    def get_faint_sound(self) -> tuple[str, float]:
        """Return the monster's faint sound effect and volume."""
        cfg = self.monster.sound_config
        call = cfg.faint

        if isinstance(call, SoundProperties):
            sfx = call.sfx if call.sfx is not None else cfg.default_faint
            volume = float(call.volume)
            return sfx, volume

        return cfg.default_faint, 1.0
