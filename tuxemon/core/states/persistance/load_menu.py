import logging
from collections import namedtuple

from core import prepare
from core.components import save
from .save_menu import SaveMenuState

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


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
            self.game.player1 = prepare.player1
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
            # self.game.current_state.change_map(save_data['current_map'])

            # teleport the player to the correct position using an event engine action
            tele_x = str(int(save_data['tile_pos'][0]))
            tele_y = str(int(save_data['tile_pos'][1]))
            Action = namedtuple("action", ["type", "parameters"])
            action = Action("teleport", [save_data['current_map'], tele_x, tele_y])

            self.game.event_engine.actions['teleport']['method'](self.game, action)
