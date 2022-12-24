from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState


class ReplacingMoveActionParameters(NamedTuple):
    pass


@final
class ReplacingMoveAction(EventAction[ReplacingMoveActionParameters]):
    """
    Select a monster in the player party for forgetting a move.

    Script usage:
        .. code-block::

            replacing_move

    """

    name = "replacing_move"
    param_class = ReplacingMoveActionParameters

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        if len(menu_item.game_object.moves) > 1:
            self.player.game_variables[
                "monster_remove_moves"
            ] = menu_item.game_object.instance_id.hex
            self.session.client.pop_state()

    def start(self) -> None:
        self.player = self.session.player

        # pull up the monster menu
        menu = self.session.client.push_state(MonsterMenuState)
        for t in self.player.monsters:
            if len(t.moves) > 1:
                menu.on_menu_selection = self.set_var

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
