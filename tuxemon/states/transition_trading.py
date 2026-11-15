# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon import tools
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BLACK_COLOR, WHITE_COLOR
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

TOTAL_SECONDS: int = 8
INTERVAL_MULTIPLIER: int = 2
ITERATION_TIME: float = 0.25

PHASE_1_END = 12.5
PHASE_2_END = 37.5
PHASE_3_END = 75.0


class TradingTransition(State):
    """The state responsible for the trading transition."""

    name: ClassVar[str] = "TradingTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        sent_monster: str,
        received_monster: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)

        self.sent_monster = sent_monster
        self.received_monster = received_monster

        if not self.sent_monster or not self.received_monster:
            logger.error("A monster object was not provided.")
            return

        self.sent_sprite = self._load_sprite(self.sent_monster)
        self.received_sprite = self._load_sprite(self.received_monster)

        self.elapsed_time = 0.0
        self.dialog_opened = False
        self.percentage = 0.0
        self.total_seconds = TOTAL_SECONDS

        self.sent_sprite_copy = self.sent_sprite.image.copy()
        self.received_sprite_copy = self.received_sprite.image.copy()
        self.sent_sprite_white = self._white_image(
            self.sent_sprite.image.copy()
        )
        self.received_sprite_white = self._white_image(
            self.received_sprite.image.copy()
        )

        self.phase_sprites = {
            1: self.sent_sprite,
            2: self.sent_sprite,
            3: self._get_phase_3_sprite(),
            4: self.received_sprite,
        }

        screen_width, screen_height = self.client.context.resolution
        sprite_width, sprite_height = self.sent_sprite.image.get_size()
        self.sent_x = (screen_width // 4) - (sprite_width // 2)
        self.received_x = (3 * screen_width // 4) - (sprite_width // 2)
        self.sprite_y = (screen_height - sprite_height) // 2

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
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
        self.sent_sprite.image = self.sent_sprite_copy

    def _phase2(self) -> None:
        fade_amount = (self.elapsed_time - 1) / 2
        self.sent_sprite.image.blit(self.sent_sprite_copy, (0, 0))
        self.sent_sprite_white.set_alpha(int(255 * fade_amount))
        self.sent_sprite.image.blit(self.sent_sprite_white, (0, 0))

    def _phase3(self) -> None:
        iteration = int(
            (self.elapsed_time - 3) / (ITERATION_TIME / INTERVAL_MULTIPLIER)
        )
        if iteration % (2 * INTERVAL_MULTIPLIER) < INTERVAL_MULTIPLIER:
            self.sent_sprite.image = self.sent_sprite_white.copy()
            self.sent_sprite.image.set_alpha(255)
            self.received_sprite.image = self.received_sprite_white.copy()
            self.received_sprite.image.set_alpha(0)
        else:
            self.sent_sprite.image = self.sent_sprite_white.copy()
            self.sent_sprite.image.set_alpha(0)
            self.received_sprite.image = self.received_sprite_white.copy()
            self.received_sprite.image.set_alpha(255)

    def _phase4(self) -> None:
        fade_amount = (self.elapsed_time - 6) / (self.total_seconds - 6)
        self.received_sprite_white.set_alpha(int(255 * (1 - fade_amount)))

        self.received_sprite.image.blit(self.received_sprite_copy, (0, 0))
        self.received_sprite.image.blit(self.received_sprite_white, (0, 0))

        if self.elapsed_time > self.total_seconds and not self.dialog_opened:
            self.client.sound_manager.play("sound_confirm")
            self.on_animation_complete()

    def draw(self, surface: Surface) -> None:
        surface.fill(BLACK_COLOR)

        # In phases 1 and 2, only the sent monster is displayed, centered
        if self.phase in (1, 2):
            sprite_image = self.sent_sprite.image
            width, _ = self.client.context.resolution
            center_x = (width - sprite_image.get_width()) // 2
            surface.blit(sprite_image, (center_x, self.sprite_y))
        # In phases 3 and 4, both sprites are displayed at their respective positions
        elif self.phase in (3, 4):
            surface.blit(self.sent_sprite.image, (self.sent_x, self.sprite_y))
            surface.blit(
                self.received_sprite.image, (self.received_x, self.sprite_y)
            )

    def _load_sprite(self, slug: str) -> Sprite:
        monster = MonsterModel.lookup(slug, db)
        loader = SpriteLoader()
        sprites = monster.sprites
        assert sprites
        handler = MonsterSpriteHandler(
            slug=slug,
            sheet_path=loader.resolve_path(sprites.sheet),
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
        )
        assert handler
        return handler.get_sprite("front", self.factor)

    def _white_image(self, sprite: Surface) -> Surface:
        for x in range(sprite.get_width()):
            for y in range(sprite.get_height()):
                if sprite.get_at((x, y)).a != 0:
                    sprite.set_at((x, y), WHITE_COLOR)
        return sprite

    def on_animation_complete(self) -> None:
        if self.sent_sprite.image:
            self.sent_sprite.image.set_alpha(255)
        self.sent_sprite.image = None

        self.received_sprite.image = self.received_sprite_copy
        self.received_sprite.image.set_alpha(255)

        param = {
            "sent": T.format(self.sent_monster),
            "received": T.format(self.received_monster),
        }
        msg = T.format("trade_completed", param)
        tools.open_dialog(self.client, [msg], dialog_speed="max")
        self.dialog_opened = True

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            if self.percentage < 100:
                self.elapsed_time = self.total_seconds
            else:
                self.client.current_music.unpause()
                self.client.pop_state()
        return None

    def _get_phase_3_sprite(self) -> Sprite:
        iteration = int(
            (self.elapsed_time - 3) / (ITERATION_TIME / INTERVAL_MULTIPLIER)
        )
        return (
            self.sent_sprite
            if iteration % (2 * INTERVAL_MULTIPLIER) < INTERVAL_MULTIPLIER
            else self.received_sprite
        )
