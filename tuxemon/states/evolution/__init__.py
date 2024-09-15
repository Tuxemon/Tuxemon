# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import pygame
from pygame import Surface

from tuxemon import prepare, tools
from tuxemon.db import MonsterModel, db
from tuxemon.graphics import load_sprite
from tuxemon.locale import T
from tuxemon.platform.const import buttons
from tuxemon.session import local_session
from tuxemon.state import State

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

TOTAL_SECONDS: int = 8
INTERVAL_MULTIPLIER: int = 2
ITERATION_TIME: float = 0.25

PHASE_1_END = 12.5
PHASE_2_END = 37.5
PHASE_3_END = 75.0


class EvolutionTransition(State):
    """The state responsible for the evolution transition."""

    force_draw = True

    def __init__(
        self,
        original: str,
        evolved: str,
    ) -> None:
        super().__init__()
        self.original_monster = self._get_monster(original)
        self.evolved_monster = self._get_monster(evolved)
        if not self.original_monster or not self.evolved_monster:
            return
        self.original = original
        self.evolved = evolved

        self.original_sprite = self._load_sprite(self.original_monster.slug)
        self.evolved_sprite = self._load_sprite(self.evolved_monster.slug)

        self.transition_start_time = pygame.time.get_ticks()
        self.dialog_opened = False
        self.elapsed_time = 0.0
        self.percentage = 0.0
        self.total_seconds = TOTAL_SECONDS
        self.original_sprite_copy = self.original_sprite.image.copy()
        self.evolved_sprite_copy = self.evolved_sprite.image.copy()
        self.original_sprite_white = self._white_image(
            self.original_sprite.image.copy()
        )
        self.evolved_sprite_white = self._white_image(
            self.evolved_sprite.image.copy()
        )

        self.phase_sprites = {
            1: self.original_sprite,
            2: self.original_sprite,
            3: self._get_phase_3_sprite(),
            4: self.evolved_sprite,
        }

        screen_width, screen_height = prepare.SCREEN_SIZE
        sprite_width, sprite_height = self.original_sprite.image.get_size()
        self.x = (screen_width - sprite_width) // 2
        self.y = (screen_height - sprite_height) // 2

    def update(self, time_delta: float) -> None:
        current_time = pygame.time.get_ticks()
        self.elapsed_time = (current_time - self.transition_start_time) / 1000
        self.percentage = (self.elapsed_time / self.total_seconds) * 100

        self.phase = 0
        if self.percentage < PHASE_1_END:
            self.phase = 1
        elif self.percentage < PHASE_2_END:
            self.phase = 2
        elif self.percentage < PHASE_3_END:
            self.phase = 3
        else:
            self.phase = 4

        phase_actions = {
            1: self._phase1,
            2: self._phase2,
            3: self._phase3,
            4: self._phase4,
        }

        phase_actions[self.phase]()

    def _phase1(self) -> None:
        self.client.current_music.pause()
        self.original_sprite.image = self.original_sprite_copy

    def _phase2(self) -> None:
        fade_amount = (self.elapsed_time - 1) / 2
        self.original_sprite.image.blit(self.original_sprite_copy, (0, 0))
        self.original_sprite_white.set_alpha(int(255 * fade_amount))
        self.original_sprite.image.blit(self.original_sprite_white, (0, 0))

    def _phase3(self) -> None:
        iteration = int(
            (self.elapsed_time - 3) / (ITERATION_TIME / INTERVAL_MULTIPLIER)
        )
        if iteration % (2 * INTERVAL_MULTIPLIER) < INTERVAL_MULTIPLIER:
            self.original_sprite.image = self.original_sprite_white.copy()
            self.original_sprite.image.set_alpha(255)
            self.evolved_sprite.image = self.evolved_sprite_white.copy()
            self.evolved_sprite.image.set_alpha(0)
        else:
            self.original_sprite.image = self.original_sprite_white.copy()
            self.original_sprite.image.set_alpha(0)
            self.evolved_sprite.image = self.evolved_sprite_white.copy()
            self.evolved_sprite.image.set_alpha(255)

    def _phase4(self) -> None:
        fade_amount = (self.elapsed_time - 6) / (self.total_seconds - 6)
        self.evolved_sprite_white.set_alpha(int(255 * (1 - fade_amount)))

        self.evolved_sprite.image.blit(self.evolved_sprite_copy, (0, 0))
        self.evolved_sprite.image.blit(self.evolved_sprite_white, (0, 0))

        if self.elapsed_time > self.total_seconds and not self.dialog_opened:
            self.client.sound_manager.play_sound("sound_confirm")
            self.on_animation_complete()

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.fill(prepare.BLACK_COLOR)
        if self.phase == 3:
            sprite = self._get_phase_3_sprite()
        else:
            sprite = self.phase_sprites[self.phase]
        sprite_image = sprite.image
        if sprite_image is None:
            return

        surface.blit(sprite_image, (self.x, self.y))

    def _get_monster(self, slug: str) -> Optional[MonsterModel]:
        if slug not in db.database["monster"]:
            logger.error(f"{slug} doesn't exist.")
            return None
        return db.lookup(slug, table="monster")

    def _load_sprite(self, slug: str) -> Sprite:
        path = tools.transform_resource_filename(
            f"gfx/sprites/battle/{slug}-front.png"
        )
        return load_sprite(path)

    def _white_image(self, sprite: Surface) -> Surface:
        for x in range(sprite.get_width()):
            for y in range(sprite.get_height()):
                if sprite.get_at((x, y)).a != 0:
                    sprite.set_at((x, y), prepare.WHITE_COLOR)
        return sprite

    def on_animation_complete(self) -> None:
        param = {
            "name": T.format(self.original),
            "evolve": T.format(self.evolved),
        }
        msg = T.format("evolution_ended", param)
        tools.open_dialog(local_session, [msg])
        self.dialog_opened = True

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            if self.percentage < 100:
                self.transition_start_time = pygame.time.get_ticks() - (
                    self.total_seconds * 1000
                )
            else:
                self.client.current_music.unpause()
                self.client.pop_state()
        return None

    def _get_phase_3_sprite(self) -> Sprite:
        iteration = int(
            (self.elapsed_time - 3) / (ITERATION_TIME / INTERVAL_MULTIPLIER)
        )
        if iteration % (2 * INTERVAL_MULTIPLIER) < INTERVAL_MULTIPLIER:
            return self.original_sprite
        else:
            return self.evolved_sprite
