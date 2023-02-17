# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import ABC, abstractmethod
from random import choice
from typing import TYPE_CHECKING, Sequence, Tuple, Union

from tuxemon.item.item import Item
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


# Class definition for an AI model.
# TODO: allow AI to target self or own team
class AI(ABC):
    """Base class for an AI model object."""

    @abstractmethod
    def make_decision_trainer(
        self,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Technique, Monster]:
        """
        Given a npc, and list of opponents, decide an action to take.

        Parameters:
            monster: The monster whose decision is being decided.
            opponents: Sequence of possible targets.

        Returns:
            Chosen technique and target.

        """
        raise NotImplementedError

    def make_decision_wild(
        self,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Technique, Monster]:
        raise NotImplementedError


class SimpleAI(AI):
    """Very simple AI.  Always uses first technique against first opponent."""

    def make_decision_trainer(
        self,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Technique, Monster]:
        return monster.moves[0], opponents[0]

    def make_decision_wild(
        self,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Technique, Monster]:
        return monster.moves[0], opponents[0]


class RandomAI(AI):
    """AI will use random technique against random opponent."""

    def make_decision_trainer(
        self,
        user: NPC,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Union[Monster, NPC], Union[Item, Technique], Monster]:
        """
        Trainer battles.
        """
        if self.check_strongest(user, monster):
            if len(user.items) > 0:
                for itm in user.items:
                    if itm.sort == "potion":
                        if self.need_potion(monster):
                            return user, itm, monster
        technique, target = self.track_next_use(monster, opponents)
        # send data
        return monster, technique, target

    def make_decision_wild(
        self,
        user: NPC,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Union[Monster, NPC], Union[Item, Technique], Monster]:
        """
        Wild encounters.
        """
        technique, target = self.track_next_use(monster, opponents)
        # send data
        return monster, technique, target

    def track_next_use(
        self,
        monster: Monster,
        opponents: Sequence[Monster],
    ) -> Tuple[Technique, Monster]:
        """
        Tracks next_use and recharge, if both unusable, skip.
        """
        actions = []
        # it chooses among the last 4 moves
        for mov in monster.moves[-monster.max_moves :]:
            if mov.next_use <= 0:
                for opponent in opponents:
                    # it checks technique conditions
                    if mov.validate(opponent):
                        actions.append((mov, opponent))
        if not actions:
            skip = Technique("skip")
            return skip, choice(opponents)
        else:
            return choice(actions)

    def check_weakest(self, trainer: NPC, fighter: Monster) -> bool:
        """
        Is it the weakest monster in the NPC's party?
        """
        weakest = [
            m
            for m in trainer.monsters
            if m.level == min([m.level for m in trainer.monsters])
        ]
        weak = weakest[0]
        if weak.level == fighter.level:
            return True
        else:
            return False

    def check_strongest(self, trainer: NPC, fighter: Monster) -> bool:
        """
        Is it the strongest monster in the NPC's party?
        """
        strongest = [
            m
            for m in trainer.monsters
            if m.level == max([m.level for m in trainer.monsters])
        ]
        strong = strongest[0]
        if strong.level == fighter.level:
            return True
        else:
            return False

    def need_potion(self, monster: Monster) -> bool:
        """
        It checks if the current_hp are less than the 15%.
        """
        if monster.current_hp > 1 and monster.current_hp <= round(
            monster.hp * 0.15
        ):
            return True
        else:
            return False
