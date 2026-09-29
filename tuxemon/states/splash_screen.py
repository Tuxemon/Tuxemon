# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.platform.const.graphics import (
    BLACK_COLOR,
    CREATIVE_COMMONS,
    PYGAME_LOGO,
)
from tuxemon.platform.events import PlayerInput
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.state.manager import StateManager

logger = logging.getLogger(__name__)


class SplashState(State):
    """The state responsible for the splash screen."""

    name: ClassVar[str] = "SplashState"
    default_duration = 3

    def __init__(
        self, client: BaseClient, parent: StateManager, **kwargs: Any
    ) -> None:
        super().__init__(client=client, **kwargs)

        self.parent = parent

        # this task will skip the splash screen after some time
        self.task(self.fade_out, interval=self.default_duration)
        self.triggered = False

        width, height = client.context.resolution

        # The space between the edge of the screen
        splash_border = int(width / 20)

        # Set up the splash screen logos
        logo = self.load_sprite(PYGAME_LOGO)
        logo.rect.topleft = (
            splash_border,
            height - splash_border - logo.rect.height,
        )

        # Set up the splash screen logos
        cc = self.load_sprite(CREATIVE_COMMONS)
        cc.rect.topleft = (
            width - splash_border - cc.rect.width,
            height - splash_border - cc.rect.height,
        )
        self.client.sound_manager.play("sound_ding")

    def resume(self) -> None:
        if self.triggered:
            self.parent.pop_state()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # Skip the splash screen if a key is pressed.
        if event.pressed and not self.triggered:
            self.fade_out()
        return None

    def draw(self, surface: Surface) -> None:
        if not self.triggered:
            surface.fill(BLACK_COLOR)
            self.sprites.draw(surface)

    def fade_out(self) -> None:
        self.triggered = True
        self.parent.push_state("FadeOutTransition")
