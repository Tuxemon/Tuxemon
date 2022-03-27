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
# states.SetKeyState Handles the input change screen 
# states.ControlState Handles the list of inputs to change screen
#
"""This module contains the Options state"""
from __future__ import annotations

from functools import partial
from typing import Any, Callable, Generator, Union, Optional

import pygame

from tuxemon import prepare, config
from tuxemon.constants import paths
from tuxemon.event.eventengine import EventEngine
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.platform_pygame.events import PygameKeyboardInput
from tuxemon.session import local_session
from tuxemon.platform.events import PlayerInput
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

    def startup(self, **kwargs: Any) -> None:
        """
        Used when initializing the state
        """
        self.button = kwargs["button"]
        super().startup(**kwargs)

        label = T.translate(T.translate("options_new_input_key0")).upper()
        image = self.shadow_text(label)
        item = MenuItem(image, label, None, None)
        self.add(item)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # must use get_pressed because the events do not contain references to pygame events
        pressed_key = None
        arrow_keys = [
            [pygame.K_UP, "up"],
            [pygame.K_DOWN, 'down'],
            [pygame.K_RIGHT, "right"],
            [pygame.K_LEFT, "left"]
        ]
        for k in range(len(pygame.key.get_pressed())):
            if pygame.key.get_pressed()[k]: pressed_key = k

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

        is_pressed = (event.pressed or event.value == "") and pressed_key_str is not None
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
    rows = 7 # TODO: Compute it

    def startup(self, **kwargs: Any) -> None:
        """
        Used when initializing the state.
        """
        super().startup(**kwargs)
        self.reload_controls()

    def initialize_items(self) -> Generator[MenuItem[ControlStateObj], None, None]:
        def change_state(
            state: Union[State, str],
            **change_state_kwargs: Any
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state,
                state,
                **change_state_kwargs
            )
        
        display_buttons = {}
        key_names = config.get_custom_pygame_keyboard_controls_names(tuxe_config.cfg)
        for k in key_names:
            display_buttons[key_names[k]] = k

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
            (display_buttons[buttons.BACK], None)
        )

        for key, button in key_items_map:
            label = f"{T.translate(key).upper()}"
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, change_state("SetKeyState", button=button))
            item.enabled = button is not None
            self.add(item)

    def reload_controls(self):
        with open(paths.USER_CONFIG_PATH, "w") as fp:
            tuxe_config.cfg.write(fp)

        # reload inputs
        tuxe_config.keyboard_button_map = config.get_custom_pygame_keyboard_controls(tuxe_config.cfg)
        prepare.CONFIG = tuxe_config
        local_session.client.config = tuxe_config
        keyboard = PygameKeyboardInput(tuxe_config.keyboard_button_map)
        local_session.client.input_manager.set_input(0, 0, keyboard)
        local_session.client.event_engine = EventEngine(local_session)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.button == buttons.BACK:
            self.reload_controls()

        return super().process_event(event)
