# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState


@final
@dataclass
class BreedingAction(EventAction):
    """
    Select a monster in the player party filtered by gender and store its
    id in a variables (breeding_father or breeding_mother)

    Script usage:
        .. code-block::

            breeding <gender>

    Script parameters:
        gender: Gender (male or female).

    """

    name = "breeding"
    gender: str

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        if self.gender == "male":
            if menu_item.game_object.gender == self.gender:
                self.player.game_variables[
                    "breeding_father"
                ] = menu_item.game_object.instance_id.hex
                self.session.client.pop_state()
        elif self.gender == "female":
            if menu_item.game_object.gender == self.gender:
                self.player.game_variables[
                    "breeding_mother"
                ] = menu_item.game_object.instance_id.hex
                self.session.client.pop_state()

    def start(self) -> None:
        self.player = self.session.player

        # pull up the monster menu
        menu = self.session.client.push_state(MonsterMenuState())
        for t in self.player.monsters:
            if t.gender == self.gender:
                menu.on_menu_selection = self.set_var

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
