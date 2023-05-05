# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Tuple

from tuxemon.combat import has_status
from tuxemon.db import ItemCategory, PlagueType
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState


# Class definition for an AI model.
class AI:
    def __init__(self, combat: CombatState, monster: Monster) -> None:
        super().__init__()
        self.combat = combat
        self.human = combat.players[0]  # human
        self.user = combat.players[1]  # ai
        self.monster = monster
        self.opponents = combat.monsters_in_play[self.human]

        if self.combat.is_trainer_battle:
            self.make_decision_trainer()
        else:
            self.make_decision_wild()

    def make_decision_trainer(self) -> None:
        """
        Trainer battles.
        """
        if self.check_strongest():
            if len(self.user.items) > 0:
                for itm in self.user.items:
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

    def track_next_use(self) -> Tuple[Technique, Monster]:
        """
        Tracks next_use and recharge, if both unusable, skip.
        """
        actions = []
        # it chooses among the last 4 moves
        for mov in self.monster.moves[-self.monster.max_moves :]:
            if mov.next_use <= 0:
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

    def check_weakest(self) -> bool:
        """
        Is it the weakest monster in the NPC's party?
        """
        weakest = [
            m
            for m in self.user.monsters
            if m.level == min([m.level for m in self.user.monsters])
        ]
        weak = weakest[0]
        if weak.level == self.monster.level:
            return True
        else:
            return False

    def check_strongest(self) -> bool:
        """
        Is it the strongest monster in the NPC's party?
        """
        strongest = [
            m
            for m in self.user.monsters
            if m.level == max([m.level for m in self.user.monsters])
        ]
        strong = strongest[0]
        if strong.level == self.monster.level:
            return True
        else:
            return False

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
        # null action for dozing
        if has_status(self.monster, "status_dozing"):
            status = Technique()
            status.load("status_dozing")
            technique = status
        # null action for plague - spyder_bite
        if self.monster.plague == PlagueType.infected:
            value = random.randint(1, 8)
            if value == 1:
                status = Technique()
                status.load("status_spyderbite")
                technique = status
                if self.monster.plague == PlagueType.infected:
                    target.plague = PlagueType.infected
        # check status response
        if self.combat.status_response_technique(self.monster, technique):
            self._lost_monster = self.monster
        self.combat.enqueue_action(self.monster, technique, target)

    def action_item(self, item: Item) -> None:
        """
        Send action item.
        """
        if self.combat.status_response_item(self.monster):
            self._lost_monster = self.monster
        self.combat.enqueue_action(self.user, item, self.monster)
