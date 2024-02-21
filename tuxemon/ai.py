# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tuxemon.combat import pre_checking, recharging
from tuxemon.db import ItemCategory
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import CombatState


# Class definition for an AI model.
class AI:
    def __init__(
        self, combat: CombatState, monster: Monster, character: NPC
    ) -> None:
        super().__init__()
        self.combat = combat
        self.character = character
        self.monster = monster
        if character == combat.players[0]:
            self.opponents = combat.monsters_in_play[combat.players[1]]
        if character == combat.players[1]:
            self.opponents = combat.monsters_in_play[combat.players[0]]

        if self.combat.is_trainer_battle:
            self.make_decision_trainer()
        else:
            self.make_decision_wild()

    def make_decision_trainer(self) -> None:
        """
        Trainer battles.
        """
        if len(self.character.items) > 0:
            for itm in self.character.items:
                if itm.category == ItemCategory.potion:
                    if self.need_potion():
                        self.action_item(itm)
        technique, target = self.track_next_use()
        # send data
        self.action_tech(technique, target)

    def make_decision_wild(self) -> None:
        """
        Wild encounters.
        """
        technique, target = self.track_next_use()
        # send data
        self.action_tech(technique, target)

    def track_next_use(self) -> tuple[Technique, Monster]:
        """
        Tracks next_use and recharge, if both unusable, skip.
        """
        actions = []
        # it chooses among the last 4 moves
        for mov in self.monster.moves[-self.monster.max_moves :]:
            if not recharging(mov):
                for opponent in self.opponents:
                    # it checks technique conditions
                    if mov.validate(opponent):
                        actions.append((mov, opponent))
        if not actions:
            skip = Technique()
            skip.load("skip")
            return skip, random.choice(self.opponents)
        else:
            return random.choice(actions)

    def need_potion(self) -> bool:
        """
        It checks if the current_hp are less than the 15%.
        """
        if self.monster.current_hp > 1 and self.monster.current_hp <= round(
            self.monster.hp * 0.15
        ):
            return True
        else:
            return False

    def action_tech(self, technique: Technique, target: Monster) -> None:
        """
        Send action tech.
        """
        self.character.game_variables["action_tech"] = technique.slug
        technique = pre_checking(self.monster, technique, target, self.combat)
        self.combat.enqueue_action(self.monster, technique, target)

    def action_item(self, item: Item) -> None:
        """
        Send action item.
        """
        self.combat.enqueue_action(self.character, item, self.monster)
