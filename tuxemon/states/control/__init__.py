#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Andrew Hong <novialriptide@gmail.com>
#
#
# states.start Handles the start screen which loads and creates new games
#
"""This module contains the Options state
"""
from __future__ import annotations

from functools import partial
from typing import Any, Callable, Union, Optional

import pygame

from tuxemon import prepare, config
from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.platform_pygame.events import PygameMouseInput, PygameGamepadInput, PygameTouchOverlayInput, PygameKeyboardInput, PygameEventQueueHandler
from tuxemon.session import local_session
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

ControlStateObj = Callable[[], object]
tuxe_config = config.TuxemonConfig(paths.USER_CONFIG_PATH)
pre_config = prepare.CONFIG

class SetKeyState(PopUpMenu):
    """
    This state is responsible for setting the input keys. 
    This only works for pygame events
    """
    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        self.input = kwargs["input"]
        super().startup(**kwargs)

        menu_items_map = (
            T.translate("options_new_input_key0"),
            T.translate("options_new_input_key1")
        )

        for key in menu_items_map:
            label = T.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, None)
            self.add(item)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # must use get_pressed because the events do not contain references to pygame events
        pressed_key = None
        if pygame.key.get_pressed()[pygame.K_UP]: pressed_key = "up"
        if pygame.key.get_pressed()[pygame.K_DOWN]: pressed_key = "down"
        if pygame.key.get_pressed()[pygame.K_RIGHT]: pressed_key = "right"
        if pygame.key.get_pressed()[pygame.K_LEFT]: pressed_key = "left"
        for k in range(len(pygame.key.get_pressed())):
            if pygame.key.get_pressed()[k]: pressed_key = k
        if pressed_key is not None and event.pressed or event.value == "": 
            # TODO: fix or rewrite PlayerInput
            # event.value is being compared here since sometimes the value just returns an empty 
            # string and event.pressed doesn't return True when a key is being pressed
            if isinstance(pressed_key, str): pressed_key_str = pressed_key
            if isinstance(pressed_key, int): pressed_key_str = pygame.key.name(pressed_key)

            tuxe_config.cfg.set("controls", self.input, pressed_key_str)
            with open(paths.USER_CONFIG_PATH, "w") as fp:
                tuxe_config.cfg.write(fp)

            # reload inputs
            tuxe_config.keyboard_button_map = config.get_custom_pygame_keyboard_controls(tuxe_config.cfg)

            keyboard = PygameKeyboardInput(pre_config.keyboard_button_map)
            local_session.client.input_manager.set_input(0, 0, keyboard)
            print(local_session.client.input_manager._inputs[0])
            
            prepare.CONFIG = tuxe_config
            local_session.client.config = tuxe_config

            self.client.replace_state(ControlState)
            self.close()

        super().process_event(event)

class ControlState(PopUpMenu[ControlStateObj]):
    """
    This state is responsible for the option menu
    """
    escape_key_exits = True
    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        # TODO: update the menu once a control key has been changed
        # TODO: remove the need to restart the game for changes to take place
        super().startup(**kwargs)

        def change_state(state: Union[State, str], **change_state_kwargs: Any) -> Callable[[], State]:
            return partial(self.client.push_state, state, **change_state_kwargs)

        display_buttons = {}
        key_names = config.get_custom_pygame_keyboard_controls_names(tuxe_config.cfg)
        for button in key_names:
            if button is not None:
                display_buttons[key_names[button]] = button
        key_items_map = (
            ("menu_up_key", "up", display_buttons[buttons.UP]),
            ("menu_left_key", "left", display_buttons[buttons.LEFT]),
            ("menu_right_key", "right", display_buttons[buttons.RIGHT]),
            ("menu_down_key", "down", display_buttons[buttons.DOWN]),
            ("menu_primary_select_key", "a", display_buttons[buttons.A]),
            ("menu_secondary_select_key", "b", display_buttons[buttons.B]),
            ("menu_back_key", "back", display_buttons[buttons.BACK])
        )

        for key, key1, current_input in key_items_map:
            label = f"{T.translate(key).upper()} | {current_input}"
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, change_state(SetKeyState, input=key1))
            self.add(item)
