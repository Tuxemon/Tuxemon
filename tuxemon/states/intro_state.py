# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.animation_entity import AnimationManager
from tuxemon.db import LoopMode
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const.graphics import BLACK_COLOR

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class IntroState(PopUpMenu[Callable[[], None]]):
    """The state responsible for the splash screen."""

    name: ClassVar[str] = "IntroState"

    def __init__(self, client: BaseClient, **kwargs: Any) -> None:
        super().__init__(client=client, **kwargs)

        self.triggered = False
        self.anim_manager = AnimationManager()

        try:
            intro_sprite = self.anim_manager.get_sprite(
                slug="intro", loop=LoopMode.INFINITE
            )

            self.sprites.add(intro_sprite)

            self.client.current_music.play("music_main_theme")

        except Exception as e:
            logger.warning(f"Could not load intro animation: {e}. Skipping.")
            self.client.replace_state("StartState")

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        if event.pressed and not self.triggered:
            self.client.replace_state("StartState")
        return None

    def update(self, dt: float) -> None:
        super().update(dt)
        self.sprites.update(dt)

    def draw(self, surface: Surface) -> None:
        if not self.triggered:
            surface.fill(BLACK_COLOR)
            self.sprites.draw(surface)
            label = self.shadow_text(T.translate("menu_intro"))
            rect = surface.get_rect()
            label_rect = label.get_rect(center=(rect.centerx, rect.height // 4))
            surface.blit(label, label_rect)
