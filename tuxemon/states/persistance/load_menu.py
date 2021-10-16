from __future__ import annotations
import logging

from tuxemon import save, prepare
from .save_menu import SaveMenuState
from tuxemon.session import local_session
from typing import Any, Optional
from tuxemon.menu.interface import MenuItem

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
            # TODO: Get player from whatever place and use self.client in
            # order to build a Session
            local_session.player.set_state(local_session, save_data)

            old_world = self.client.get_state_by_name("WorldState")
            if old_world is None:
                # when game is loaded from the start menu
                self.client.pop_state()  # close this menu
                self.client.pop_state()  # close the start menu
            else:
                # when game is loaded from world menu
                self.client.pop_state(self)
                self.client.pop_state(old_world)

            map_path = prepare.fetch("maps", save_data["current_map"])
            self.client.push_state(
                "WorldState",
                map_name=map_path,
            )

            # teleport the player to the correct position using an event
            # engine action
            tele_x, tele_y = save_data["tile_pos"]
            params = [save_data["current_map"], tele_x, tele_y]
            self.client.event_engine.execute_action("teleport", params)
