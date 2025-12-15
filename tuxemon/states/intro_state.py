# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional

from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.graphics import load_animated_sprite
from tuxemon.locale import T
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.tools import transform_resource_filename

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)
MenuGameObj = Callable[[], None]


class IntroState(PopUpMenu[MenuGameObj]):
    """The state responsible for the splash screen."""

    name: ClassVar[str] = "IntroState"

    _cached_sprites = None

    def __init__(self) -> None:
        super().__init__()

        self.triggered: bool = False

        if IntroState._cached_sprites is None:
            IntroState._cached_sprites = self._load_sprites()
        if IntroState._cached_sprites:
            self.sprites.add(IntroState._cached_sprites)

    def _load_sprites(self) -> Optional[Sprite]:
        """Helper function to load the animation sprites dynamically using pathlib."""
        folder_path = Path(transform_resource_filename("animations/intro"))

        if not folder_path.is_dir():
            logger.warning("Intro folder not found. Skipping intro.")
            self.client.replace_state("StartState")
            return None

        sprite_files = sorted(
            [
                str(file_path)
                for file_path in folder_path.glob("intro_*.png")
                if file_path.is_file()
            ]
        )

        if not sprite_files:
            logger.warning("Intro folder is empty. Skipping intro.")
            self.client.replace_state("StartState")
            return None

        try:
            sprite = load_animated_sprite(sprite_files, 0.07)
            self.client.current_music.play("music_main_theme")
            return sprite
        except ValueError as e:
            logger.error(f"Failed to load animated sprite: {e}")
            self.client.replace_state("StartState")
            return None

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.pressed and not self.triggered:
            self.client.replace_state("StartState")
        return None

    def draw(self, surface: Surface) -> None:
        if not self.triggered:
            surface.fill(prepare.BLACK_COLOR)
            self.sprites.draw(surface)
            label = self.shadow_text(T.translate("menu_intro"))
            label_rect = label.get_rect(midbottom=surface.get_rect().center)
            surface.blit(label, label_rect)
