from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from tuxemon.core import save
from .save_menu import SaveMenuState

logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def startup(self, *items, **kwargs):
        if 'selected_index' not in kwargs:
            kwargs['selected_index'] = save.slot_number or 0
        super(LoadMenuState, self).startup(*items, **kwargs)
        slot = kwargs.get("load_slot")
        if slot:
            self.selected_index = slot - 1
            self.on_menu_selection(None)

    def on_menu_selection(self, menuitem):
        save_data = save.load(self.selected_index + 1)
        if save_data and "error" not in save_data:
            self.game.player1.set_state(self.game, save_data)

            old_world = self.game.get_state_name("WorldState")
            if old_world is None:
                # when game is loaded from the start menu
                self.game.pop_state()  # close this menu
                self.game.pop_state()  # close the start menu
            else:
                # when game is loaded from world menu
                self.game.pop_state(self)
                self.game.pop_state(old_world)

            self.game.push_state("WorldState")

            # teleport the player to the correct position using an event engine action
            tele_x, tele_y = save_data['tile_pos']
            params = [save_data['current_map'], tele_x, tele_y]
            self.game.event_engine.execute_action('teleport', params)
