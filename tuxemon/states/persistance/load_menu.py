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
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.LoadMenuState
#
from __future__ import annotations

import logging
from typing import Any, Optional

from tuxemon import prepare, save
from tuxemon.db import db
from tuxemon.menu.interface import MenuItem
from tuxemon.session import local_session
from tuxemon.states.world.worldstate import WorldState

from .save_menu import SaveMenuState

logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def startup(self, **kwargs: Any) -> None:
        if "selected_index" not in kwargs:
            kwargs["selected_index"] = save.slot_number or 0
        super().startup(**kwargs)
        slot = kwargs.get("load_slot")
        if slot:
            self.selected_index = slot - 1
            self.on_menu_selection(None)

    def on_menu_selection(self, menuitem: Optional[MenuItem[None]]) -> None:
        save_data = save.load(self.selected_index + 1)
        if save_data and "error" not in save_data:

            try:
                old_world = self.client.get_state_by_name(WorldState)
                # when game is loaded from world menu
                self.client.pop_state(self)
                self.client.pop_state(old_world)
            except ValueError:
                # when game is loaded from the start menu
                self.client.pop_state()
                self.client.pop_state()

            filename = save_data["current_map"]
            map_path = prepare.fetch("maps", db.lookup_file("maps", filename))
            self.client.push_state(
                WorldState,
                map_name=map_path,
            )

            # TODO: Get player from whatever place and use self.client in
            # order to build a Session
            local_session.player.set_state(local_session, save_data)

            # teleport the player to the correct position using an event
            # engine action
            tele_x, tele_y = save_data["tile_pos"]
            params = [save_data["current_map"], tele_x, tele_y]
            self.client.event_engine.execute_action("teleport", params)
