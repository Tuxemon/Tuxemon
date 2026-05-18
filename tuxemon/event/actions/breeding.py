# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.filter import MonsterFilter
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.states.monster_menu import MonsterMenuState

logger = logging.getLogger(__name__)


@final
@dataclass
class BreedingAction(EventAction):
    """
    Select a monster in the player party filtered by gender and store its
    id in a variables (breeding_father or breeding_mother)

    Script usage:
        .. code-block::

            breeding <character>,<gender>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        gender: Gender (male or female).
    """

    name = "breeding"
    character: str
    gender: str

    def set_var(self, menu_item: MenuItem[Monster | None]) -> None:
        monster = menu_item.game_object
        if monster is None:
            self.stop()
            return

        parent = (
            "breeding_mother" if self.gender == "female" else "breeding_father"
        )
        self.char.game_variables.set(parent, monster.instance_id.hex)
        self.session.client.pop_state()

    def start(self, session: Session) -> None:
        self.session = session
        char = session.get_npc(self.character)

        if not char:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        self.char = char

        monster_filter = MonsterFilter()
        monster_filter.set_filter_custom_and(
            lambda m: m.gender.value == self.gender,
            lambda m: m.stage.value != "basic",
        )

        valid_monsters = monster_filter.get_filtered_monsters(
            self.char.monsters
        )
        if not valid_monsters:
            logger.error(f"No {self.gender} monsters available for breeding.")
            self.stop()
            return

        session.client.push_state(
            MonsterMenuState(
                session.client,
                self.char.monsters,
                monster_filter,
                on_selection=self.set_var,
            )
        )

    def update(self, session: Session, dt: float) -> None:
        if "MonsterMenuState" not in session.client.active_state_names:
            self.stop()
