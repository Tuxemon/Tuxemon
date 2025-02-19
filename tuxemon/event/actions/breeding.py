# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

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

    def validate(self, target: Optional[Monster]) -> bool:
        if target:
            if target.gender == self.gender and target.stage != "basic":
                return True
        return False

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        player = self.session.player
        monster = menu_item.game_object

        parent = (
            "breeding_mother" if self.gender == "female" else "breeding_father"
        )
        player.game_variables[parent] = str(monster.instance_id.hex)
        self.session.client.pop_state()

    def start(self) -> None:
        # pull up the monster menu so we know which one we are saving
        menu = self.session.client.push_state(MonsterMenuState())
        menu.is_valid_entry = self.validate  # type: ignore[assignment]
        menu.on_menu_selection = self.set_var  # type: ignore[assignment]

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
