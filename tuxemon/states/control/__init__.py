# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Options state"""
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Optional, Union

import pygame
import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import config, prepare, tools
from tuxemon.constants import paths
from tuxemon.event.eventengine import EventEngine
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput
from tuxemon.session import local_session
from tuxemon.state import State

tuxe_config = config.TuxemonConfig(paths.USER_CONFIG_PATH)
pre_config = prepare.CONFIG

METRIC = "Metric"
IMPERIAL = "Imperial"
NORTHERN = "Northern"
SOUTHERN = "Southern"


class SetKeyState(PygameMenuState):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    def __init__(self, button: Optional[str]) -> None:
        """
        Used when initializing the state
        """
        width, height = prepare.SCREEN_SIZE

        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.2 * height)
        super().__init__(height=height, width=width)

        self.menu.add.label(T.translate("options_new_input_key0").upper())
        self.button = button
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.widget_alignment = locals.ALIGN_LEFT

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # must use get_pressed because the events do not contain references to pygame events
        pressed_key: Optional[int] = None
        for k in range(len(pygame.key.get_pressed())):
            if pygame.key.get_pressed()[k]:
                pressed_key = k

        # to prevent a KeyError from happening, the game won't let you
        # input a key if that key has already been set a value
        invalid_keys: list[int] = []
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

        is_pressed = (
            event.pressed or event.value == ""
        ) and pressed_key is not None
        if (
            isinstance(pressed_key, int)
            and is_pressed
            and pressed_key not in invalid_keys
        ):
            # TODO: fix or rewrite PlayerInput
            # event.value is being compared here since sometimes the
            # value just returns an empty string and event.pressed doesn't
            # return True when a key is being pressed
            assert self.button and pressed_key
            local_session.client.pop_state()
            pressed_key_str = pygame.key.name(pressed_key)
            if event.value == pressed_key_str:
                return event
            else:
                return None
        else:
            return None


class ControlState(PygameMenuState):
    """
    This state is responsible for the option menu.
    """

    def __init__(self) -> None:
        """
        Used when initializing the state.
        """
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.initialize_items(self.menu)
        self.reload_controls()
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT

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

        default_music: int = 50
        default_sound: int = 20
        default_unit: int = 0
        default_hemi: int = 0
        if player:
            default_music = int(
                float(player.game_variables["music_volume"]) * 100
            )
            default_sound = int(
                float(player.game_variables["sound_volume"]) * 100
            )
            if player.game_variables["unit_measure"] == METRIC:
                default_unit = 0
            elif player.game_variables["unit_measure"] == IMPERIAL:
                default_unit = 1
            if player.game_variables["hemisphere"] == NORTHERN:
                default_hemi = 0
            elif player.game_variables["hemisphere"] == SOUTHERN:
                default_hemi = 1

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
                player.game_variables["music_volume"] = round(val / 100, 1)

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
            default=default_unit,
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
            default=default_hemi,
            style="fancy",
            onchange=on_change_hemisphere,
            font_size=self.font_size_small,
        )

    def reload_controls(self) -> None:
        with open(paths.USER_CONFIG_PATH, "w") as fp:
            tuxe_config.cfg.write(fp)

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

        return super().process_event(event)
