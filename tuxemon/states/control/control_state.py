# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Optional, Union

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.event.eventengine import EventEngine
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput
from tuxemon.session import local_session
from tuxemon.state import State


class ControlState(PygameMenuState):
    """
    This state is responsible for the option menu.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Used when initializing the state.
        """
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        self.main_menu = "main_menu" in kwargs and kwargs["main_menu"]
        kwargs.pop("main_menu", None)
        super().__init__(**kwargs)
        self.initialize_items(self.menu)
        self.reload_controls()
        self.reset_theme()

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def change_state(
            state: Union[State, str], **change_state_kwargs: Any
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state, state, **change_state_kwargs
            )

        menu.select_widget(None)

        menu.add.button(
            title=T.translate("menu_up_key").upper(),
            action=change_state("SetKeyState", value="up"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_left_key").upper(),
            action=change_state("SetKeyState", value="left"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_right_key").upper(),
            action=change_state("SetKeyState", value="right"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_down_key").upper(),
            action=change_state("SetKeyState", value="down"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_primary_select_key").upper(),
            action=change_state("SetKeyState", value="a"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_secondary_select_key").upper(),
            action=change_state("SetKeyState", value="b"),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_back_key").upper(),
            action=change_state("SetKeyState", value="back"),
            font_size=self.font_size_small,
        )

        menu.add.button(
            title=T.translate("menu_reset_default").upper(),
            action=self.client.config.reset_controls_to_default,
            font_size=self.font_size_small,
        )

        language = T.translate("menu_language").upper()
        menu.add.button(
            title=f"{language}: {self.client.config.locale.slug}",
            action=change_state("SetLanguage", main_menu=self.main_menu),
            font_size=self.font_size_small,
        )

        if not self.main_menu:

            def mute_music() -> None:
                self.client.config.update_attribute(
                    "gameplay", "music_volume", str(0)
                )
                self.client.current_music.set_volume(0)

            _volume = self.client.current_music.get_volume()
            if _volume and _volume > 0.0:
                menu.add.button(
                    title=T.translate("menu_mute_music").upper(),
                    action=mute_music,
                    font_size=self.font_size_small,
                )

            _music = self.client.config.music_volume
            default_music = int(float(_music) * 100)
            _sound = self.client.config.sound_volume
            default_sound = int(float(_sound) * 100)

            unit = self.client.config.unit_measure
            _unit = 0 if str(unit) == "metric" else 1

            hemi = self.client.config.hemisphere
            _hemi = 0 if str(hemi) == "northern" else 1

            music = menu.add.range_slider(
                title=T.translate("menu_music_volume").upper(),
                default=default_music,
                range_values=(0, 100),
                increment=10,
                rangeslider_id="menu_music_volume",
                value_format=lambda x: str(int(x)),
                font_size=self.font_size_small,
            )
            sound = menu.add.range_slider(
                title=T.translate("menu_sound_volume").upper(),
                default=default_sound,
                range_values=(0, 100),
                increment=10,
                rangeslider_id="menu_sound_volume",
                value_format=lambda x: str(int(x)),
                font_size=self.font_size_small,
            )

            def on_change_music(val: int) -> None:
                """
                Updates the value.
                """
                volume = round(val / 100, 1)
                self.client.config.update_attribute(
                    "gameplay", "music_volume", str(volume)
                )
                self.client.current_music.set_volume(volume)

            def on_change_sound(val: int) -> None:
                """
                Updates the value.
                """
                volume = round(val / 100, 1)
                self.client.config.update_attribute(
                    "gameplay", "sound_volume", str(volume)
                )

            music.set_onchange(on_change_music)
            sound.set_onchange(on_change_sound)

            def on_change_units(value: Any, label: str) -> None:
                """
                Updates the value.
                """
                self.client.config.update_attribute(
                    "gameplay", "unit_measure", label.lower()
                )

            metric = T.translate("menu_units_metric")
            imperial = T.translate("menu_units_imperial")
            units: list[tuple[Any, ...]] = []
            units = [(metric, metric), (imperial, imperial)]
            menu.add.selector(
                title=T.translate("menu_units").upper(),
                items=units,
                selector_id="unit",
                default=_unit,
                style="fancy",
                onchange=on_change_units,
                font_size=self.font_size_small,
            )

            def on_change_hemisphere(value: Any, label: str) -> None:
                """
                Updates the value.
                """
                self.client.config.update_attribute(
                    "gameplay", "hemisphere", label.lower()
                )

            north_hemi = T.translate("menu_hemisphere_north")
            south_hemi = T.translate("menu_hemisphere_south")
            hemispheres: list[tuple[Any, ...]] = []
            hemispheres = [(north_hemi, north_hemi), (south_hemi, south_hemi)]
            menu.add.selector(
                title=T.translate("menu_hemisphere").upper(),
                items=hemispheres,
                selector_id="hemisphere",
                default=_hemi,
                style="fancy",
                onchange=on_change_hemisphere,
                font_size=self.font_size_small,
            )

    def update_animation_size(self) -> None:
        width, height = prepare.SCREEN_SIZE
        widgets_size = self.menu.get_size(widget=True)
        _width, _height = widgets_size
        # block width if more than screen width
        _width = width if _width >= width else _width
        _height = height if _height >= height else _height

        self.menu.resize(
            max(1, int(_width * self.animation_size)),
            max(1, int(_height * self.animation_size)),
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

    def reload_controls(self) -> None:
        self.client.config.input.reload_input_map()
        keyboard = PygameKeyboardInput(
            self.client.config.input.keyboard_button_map
        )
        self.client.input_manager.event_queue.set_input(0, 0, keyboard)
        self.client.event_engine = EventEngine(local_session)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.button == buttons.BACK:
            self.reload_controls()
            if not self.main_menu:
                self.client.pop_state()

        return super().process_event(event)
