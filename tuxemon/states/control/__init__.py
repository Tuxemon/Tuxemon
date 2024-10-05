# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Options state"""
from __future__ import annotations

from collections.abc import Callable
from configparser import ConfigParser
from functools import partial
from typing import Any, Optional, Union

import pygame
import pygame_menu
from pygame_menu import locals

from tuxemon import config, prepare
from tuxemon.animation import Animation
from tuxemon.constants import paths
from tuxemon.event.eventengine import EventEngine
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput
from tuxemon.session import local_session
from tuxemon.state import State

tuxe_config = config.TuxemonConfig(paths.USER_CONFIG_PATH)
pre_config = prepare.CONFIG


def update_custom_pygame_keyboard_controls(
    config: ConfigParser, button: str, key: int
) -> None:
    config.set("controls", button, pygame.key.name(key))
    with open(paths.USER_CONFIG_PATH, "w") as fp:
        config.write(fp)
    # Get the current control state and reload controls
    control_state = local_session.client.get_state_by_name(ControlState)
    if isinstance(control_state, ControlState):
        control_state.reload_controls()


def reset_config_to_default() -> None:
    default_controls = {
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "a": "return",
        "b": "rshift, lshift",
        "back": "escape",
        "backspace": "backspace",
    }

    config = tuxe_config.cfg

    for button, key in default_controls.items():
        config.set("controls", button, key)

    with open(paths.USER_CONFIG_PATH, "w") as fp:
        config.write(fp)

    control_state = local_session.client.get_state_by_name(ControlState)
    if isinstance(control_state, ControlState):
        control_state.reload_controls()


class SetKeyState(PygameMenuState):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    def __init__(self, button: Optional[str], **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        super().__init__(**kwargs)
        self.menu.add.label(T.translate("options_new_input_key0").upper())
        self.button = button
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        invalid_keys = [
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_RSHIFT,
            pygame.K_LSHIFT,
            pygame.K_RETURN,
            pygame.K_ESCAPE,
            pygame.K_BACKSPACE,
        ]

        pressed_key = next(
            (
                k
                for k in range(len(pygame.key.get_pressed()))
                if pygame.key.get_pressed()[k]
            ),
            None,
        )

        if (
            isinstance(pressed_key, int)
            and (event.pressed or event.value == "")
            and pressed_key not in invalid_keys
        ):
            assert self.button and pressed_key
            self.client.pop_state()
            pressed_key_str = pygame.key.name(pressed_key)
            if event.value == pressed_key_str:
                # Update the configuration file with the new key
                update_custom_pygame_keyboard_controls(
                    tuxe_config.cfg, self.button, pressed_key
                )
                return event

        return None

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

        player = local_session.player
        display_buttons = {}
        key_names = config.get_custom_pygame_keyboard_controls_names(
            tuxe_config.cfg
        )
        for k, v in key_names.items():
            display_buttons[v] = k

        menu.select_widget(None)

        menu.add.button(
            title=T.translate("menu_up_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.UP]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_left_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.LEFT]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_right_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.RIGHT]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_down_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.DOWN]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_primary_select_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.A]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_secondary_select_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.B]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_back_key").upper(),
            action=change_state(
                "SetKeyState", button=display_buttons[buttons.BACK]
            ),
            font_size=self.font_size_small,
        )
        menu.add.button(
            title=T.translate("menu_reset_default").upper(),
            action=reset_config_to_default,
            font_size=self.font_size_small,
        )

        default_music = prepare.MUSIC_VOLUME
        default_sound = prepare.SOUND_VOLUME
        _unit: int = 0
        _hemi: int = 0
        if player:
            _music = player.game_variables.get("music_volume", default_music)
            default_music = int(float(_music) * 100)
            _sound = player.game_variables.get("sound_volume", default_sound)
            default_sound = int(float(_sound) * 100)

            unit = player.game_variables.get("unit_measure", prepare.METRIC)
            _unit = 0 if str(unit) == prepare.METRIC else 1

            hemi = player.game_variables.get("hemisphere", prepare.NORTHERN)
            _hemi = 0 if str(hemi) == prepare.NORTHERN else 1
        else:
            default_music *= 100
            default_sound *= 100

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
            if player:
                volume = round(val / 100, 1)
                self.client.current_music.set_volume(volume)
                player.game_variables["music_volume"] = volume

        def on_change_sound(val: int) -> None:
            """
            Updates the value.
            """
            if player:
                player.game_variables["sound_volume"] = round(val / 100, 1)

        music.set_onchange(on_change_music)
        sound.set_onchange(on_change_sound)

        def on_change_units(value: Any, label: str) -> None:
            """
            Updates the value.
            """
            if player:
                player.game_variables["unit_measure"] = label

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
            if player:
                player.game_variables["hemisphere"] = label

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
        tuxe_config.cfg.read(paths.USER_CONFIG_PATH)

        # reload inputs
        tuxe_config.keyboard_button_map = (
            config.get_custom_pygame_keyboard_controls(tuxe_config.cfg)
        )
        prepare.CONFIG = tuxe_config
        local_session.client.config = tuxe_config
        keyboard = PygameKeyboardInput(tuxe_config.keyboard_button_map)
        local_session.client.input_manager.set_input(0, 0, keyboard)
        local_session.client.event_engine = EventEngine(local_session)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.button == buttons.BACK:
            self.reload_controls()
            self.client.pop_state()

        return super().process_event(event)
