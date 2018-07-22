import logging

from tuxemon.core.components import save
from .save_menu import SaveMenuState

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def on_menu_selection(self, menuitem):
        save_data = save.load(self.selected_index + 1)
        if "error" not in save_data:
            self.game.player1.set_state(save_data)

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
