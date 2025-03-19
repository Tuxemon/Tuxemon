# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals

from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme


class SetLanguage(PygameMenuState):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    def __init__(self, main_menu: bool, **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        self.main_menu = main_menu
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        super().__init__(**kwargs)
        self.initialize_items(self.menu)
        self.reset_theme()

    def change_language(self, locale: str) -> None:
        T.change_language(locale)
        self.client.config.update_locale(locale)
        self.client.pop_state()
        if self.main_menu:
            self.client.pop_state()
            self.client.replace_state("StartState")
        else:
            self.client.pop_state()
            self.client.replace_state("WorldMenuState")

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        used = self.client.config.locale.slug
        languages = T.get_available_languages()
        for language in languages:
            if language != "README.md" and language != used:
                menu.add.button(
                    title=T.translate(f"language_{language.lower()}"),
                    action=partial(self.change_language, language),
                    font_size=self.font_size_small,
                )

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(
            max(1, int(widgets_size[0] * self.animation_size)),
            max(1, int(widgets_size[1] * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0
        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.update_callback = self.update_animation_size
        return ani
