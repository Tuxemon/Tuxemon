# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class GetPlayerMonsterAction(EventAction):
    """
    Select a monster in the player party and store its id in a variable.

    Script usage:
        .. code-block::

            get_player_monster <variable_name>

    Script parameters:
        variable_name: Name of the variable where to store the monster id.

    """

    name = "get_player_monster"
    variable_name: str

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        self.session.player.game_variables[
            self.variable_name
        ] = menu_item.game_object.instance_id.hex
        self.session.client.pop_state()

    def start(self) -> None:
        # pull up the monster menu so we know which one we are saving
        menu = self.session.client.push_state(MonsterMenuState())
        menu.on_menu_selection = self.set_var  # type: ignore[assignment]

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
