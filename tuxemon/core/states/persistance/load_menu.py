import logging

from core.components import save
from core.components.player import Player
from .save_menu import SaveMenuState

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def on_menu_selection(self, menuitem):
        try:
            save_data = save.load(self.selected_index + 1)

        except Exception as e:
            logger.error(e)
            save_data = dict()
            save_data["error"] = "Save file corrupted"
            logger.error("Failed loading save file.")

        if save_data is not None and "error" not in save_data:
            self.save_data = save.load(self.selected_index + 1)
            self.game.player1.game_variables = save_data['game_variables']
            self.game.player1.tile_pos = save_data['tile_pos']
            self.game.player1.inventory = save_data['inventory']
            self.game.player1.monsters = save_data['monsters']
            self.game.player1.storage = save_data['storage']
            self.game.player1.name = save_data['player_name']

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
            self.game.event_engine.execute_action('teleport', [save_data['current_map'], tele_x, tele_y])
