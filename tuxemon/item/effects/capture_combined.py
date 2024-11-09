# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import formula, prepare
from tuxemon.db import CategoryCondition as Category
from tuxemon.db import GenderType, SeenStatus, TasteWarm
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@dataclass
class CaptureCombinedEffect(ItemEffect):
    """Attempts to capture the target."""

    name = "capture_combined"
    category: str
    label: str
    lower_bound: float
    upper_bound: float

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        assert target

        # Calculate status modifier
        status_modifier = self._calculate_status_modifier(target)

        # Calculate tuxeball modifier
        tuxeball_modifier = self._calculate_tuxeball_modifier(item, target)

        # Perform shake check and capture calculation
        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            return ItemEffectResult(
                name=item.name, success=False, num_shakes=shakes, extras=[]
            )

        # Apply capture effects
        self._apply_capture_effects(item, target)

        return ItemEffectResult(
            name=item.name, success=True, num_shakes=shakes, extras=[]
        )

    def _calculate_status_modifier(self, target: Monster) -> float:
        status_modifier = prepare.STATUS_MODIFIER
        if target.status and target.status[0].category:
            status_modifier = (
                prepare.STATUS_NEGATIVE
                if target.status[0].category == Category.negative
                else prepare.STATUS_POSITIVE
            )
        return status_modifier

    def _calculate_tuxeball_modifier(
        self, item: Item, target: Monster
    ) -> float:
        """
        Calculate the status effectiveness modifier based on the opponent's
        status.
        """
        tuxeball_modifier = prepare.TUXEBALL_MODIFIER

        if self.category == "element":
            tuxeball_modifier = self._calculate_element_tuxeball_modifier(
                target
            )
        elif self.category == "gender":
            tuxeball_modifier = self._calculate_gender_tuxeball_modifier(
                target
            )
        elif self.category == "variable":
            tuxeball_modifier = self._calculate_variable_tuxeball_modifier()
        elif self.category == "gambler":
            tuxeball_modifier = self._calculate_gambler_tuxeball_modifier()
        elif self.category == "monster":
            tuxeball_modifier = self._calculate_monster_tuxeball_modifier(
                item, target
            )
        else:  # Flavored-based tuxeball
            target.taste_warm = TasteWarm(self.label)

        return tuxeball_modifier

    def _calculate_element_tuxeball_modifier(self, opponent: Monster) -> float:
        """
        Calculate the tuxeball effectiveness modifier based on the item's
        element and the opponent's type.
        """
        if opponent.types[0].slug != self.label:
            return self.lower_bound
        return self.upper_bound

    def _calculate_gender_tuxeball_modifier(self, opponent: Monster) -> float:
        """
        Calculate the tuxeball effectiveness modifier based on the item's
        gender and the opponent's gender.
        """
        if opponent.gender != GenderType(self.label):
            return self.lower_bound
        return self.upper_bound

    def _calculate_variable_tuxeball_modifier(self) -> float:
        """
        Calculate the tuxeball effectiveness modifier based on the item's
        variable and the game variables.
        """
        key, value = self.label.split(":")
        if (
            key in self.user.game_variables
            and self.user.game_variables[key] == value
        ):
            return self.upper_bound
        return self.lower_bound

    def _calculate_gambler_tuxeball_modifier(self) -> float:
        """
        Calculate the tuxeball effectiveness modifier based on the item's
        gambler category.
        """
        return random.uniform(self.lower_bound, self.upper_bound)

    def _calculate_monster_tuxeball_modifier(
        self, item: Item, target: Monster
    ) -> float:
        """
        Calculate the tuxeball effectiveness modifier based on the item's
        monster category.
        """
        assert item.combat_state
        our_monster = item.combat_state.monsters_in_play[self.user]

        if not our_monster:
            return prepare.TUXEBALL_MODIFIER

        monster = our_monster[0]

        if not monster.types or not monster.types:
            return prepare.TUXEBALL_MODIFIER

        if self.label == "xero":
            return (
                self.upper_bound
                if monster.types[0].slug != target.types[0].slug
                else self.lower_bound
            )
        elif self.label == "omni":
            return (
                self.lower_bound
                if monster.types[0].slug != target.types[0].slug
                else self.upper_bound
            )
        else:
            return prepare.TUXEBALL_MODIFIER

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        assert item.combat_state

        if (
            target.slug in self.user.tuxepedia
            and self.user.tuxepedia[target.slug] == SeenStatus.seen
        ):
            item.combat_state._new_tuxepedia = True
        self.user.tuxepedia[target.slug] = SeenStatus.caught
        target.capture_device = item.slug
        target.wild = False
        self.user.add_monster(target, len(self.user.monsters))
