# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Options state"""
from __future__ import annotations

from functools import partial
from typing import Any, Callable, Generator, Optional, Union

import pygame

from tuxemon import config, prepare
from tuxemon.constants import paths
from tuxemon.event.eventengine import EventEngine
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput
from tuxemon.session import local_session
from tuxemon.state import State

ControlStateObj = Callable[[], object]
tuxe_config = config.TuxemonConfig(paths.USER_CONFIG_PATH)
pre_config = prepare.CONFIG


class SetKeyState(PopUpMenu):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    shrink_to_items = True

    def __init__(self, button: Optional[str]) -> None:
        """
        Used when initializing the state
        """
        self.button = button
        super().__init__()

        label = T.translate(T.translate("options_new_input_key0")).upper()
        image = self.shadow_text(label)
        item = MenuItem(image, label, None, None)
        self.add(item)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # must use get_pressed because the events do not contain references to pygame events
        pressed_key = None
        arrow_keys = [
            [pygame.K_UP, "up"],
            [pygame.K_DOWN, "down"],
            [pygame.K_RIGHT, "right"],
            [pygame.K_LEFT, "left"],
        ]
        for k in range(len(pygame.key.get_pressed())):
            if pygame.key.get_pressed()[k]:
                pressed_key = k

        for key in arrow_keys:
            if pygame.key.get_pressed()[key[0]]:
                pressed_key = key[1]

        # to prevent a KeyError from happening, the game won't let you
        # input a key if that key has already been set a value
        invalid_keys = []
        pressed_key_str = None
        for key, value in tuxe_config.cfg.items("controls"):
            invalid_keys.append(value)

        if isinstance(pressed_key, str):
            pressed_key_str = pressed_key
        if isinstance(pressed_key, int):
            pressed_key_str = pygame.key.name(pressed_key)

        is_pressed = (
            event.pressed or event.value == ""
        ) and pressed_key_str is not None
        if is_pressed and pressed_key_str not in invalid_keys:
            # TODO: fix or rewrite PlayerInput
            # event.value is being compared here since sometimes the
            # value just returns an empty string and event.pressed doesn't
            # return True when a key is being pressed
            tuxe_config.cfg.set("controls", self.button, pressed_key_str)
            self.client.get_state_by_name(ControlState).initialize_items()
            self.close()


class ControlState(PopUpMenu[ControlStateObj]):
    """
    This state is responsible for the option menu.
    """

    escape_key_exits = True
    shrink_to_items = True
    columns = 2
    rows = 7  # TODO: Compute it

    def __init__(self) -> None:
        """
        Used when initializing the state.
        """
        super().__init__()
        self.reload_controls()

    def initialize_items(
        self,
    ) -> None:
        def change_state(
            state: Union[State, str], **change_state_kwargs: Any
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state, state, **change_state_kwargs
            )

        display_buttons = {}
        key_names = config.get_custom_pygame_keyboard_controls_names(
            tuxe_config.cfg
        )
        for k, v in key_names.items():
            display_buttons[v] = k

        self.clear()

        # TODO: add a message that says "go back to the
        #       start menu to update controls" after changes
        #       are made
        key_items_map = (
            ("menu_up_key", "up"),
            (display_buttons[buttons.UP], None),
            ("menu_left_key", "left"),
            (display_buttons[buttons.LEFT], None),
            ("menu_right_key", "right"),
            (display_buttons[buttons.RIGHT], None),
            ("menu_down_key", "down"),
            (display_buttons[buttons.DOWN], None),
            ("menu_primary_select_key", "a"),
            (display_buttons[buttons.A], None),
            ("menu_secondary_select_key", "b"),
            (display_buttons[buttons.B], None),
            ("menu_back_key", "back"),
            (display_buttons[buttons.BACK], None),
        )

        for key, button in key_items_map:
            label = f"{T.translate(key).upper()}"
            image = self.shadow_text(label)
            item = MenuItem(
                image, label, None, change_state("SetKeyState", button=button)
            )
            item.enabled = button is not None
            self.add(item)

    def reload_controls(self):
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
