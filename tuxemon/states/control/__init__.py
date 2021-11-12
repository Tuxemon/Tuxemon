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
\
from functools import partial
from typing import Any, Callable, Union, Optional

import pygame

from tuxemon import prepare, config
from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

ControlStateObj = Callable[[], object]
cfg_file = config.TuxemonConfig(paths.USER_CONFIG_PATH).cfg
config = prepare.CONFIG

def reload_control_config():
    config.a = cfg_file.get("controls", "a")
    config.b = cfg_file.get("controls", "b")
    config.up = cfg_file.get("controls", "up")
    config.left = cfg_file.get("controls", "left")
    config.down = cfg_file.get("controls", "down")
    config.right = cfg_file.get("controls", "right")
    config.back = cfg_file.get("controls", "back")

class SetKeyState(PopUpMenu):
    """This state is responsible for setting the input keys"""
    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
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

            cfg_file.set("controls", self.input, pressed_key_str)
            with open(paths.USER_CONFIG_PATH, "w") as fp:
                cfg_file.write(fp)

            self.client.replace_state(ControlState)
            self.close()

        super().process_event(event)

class ControlState(PopUpMenu[ControlStateObj]):
    """This state is responsible for the option menu"""

    escape_key_exits = True
    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
        # TODO: update the menu once a control key has been changed
        # TODO: remove the need to restart the game for changes to take place
        super().startup(**kwargs)

        def change_state(state: Union[State, str], **change_state_kwargs: Any) -> Callable[[], State]:
            return partial(self.client.push_state, state, **change_state_kwargs)

        key_items_map = (
            ("menu_up_key", "up", config.up),
            ("menu_left_key", "left", config.left),
            ("menu_right_key", "right", config.right),
            ("menu_down_key", "down", config.down),
            ("menu_primary_select_key", "a", config.a),
            ("menu_secondary_select_key", "b", config.b),
            ("menu_back_key", "back", config.back)
        )

        for key, key1, current_input in key_items_map:
            label = f"{T.translate(key).upper()} | {current_input}"
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, change_state(SetKeyState, input=key1))
            self.add(item)
