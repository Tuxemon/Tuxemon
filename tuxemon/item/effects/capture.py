# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import formula, prepare
from tuxemon.db import CategoryCondition as Category
from tuxemon.db import GenderType, SeenStatus, TasteWarm
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class CaptureEffectResult(ItemEffectResult):
    pass


@dataclass
class CaptureEffect(ItemEffect):
    """Attempts to capture the target."""

    name = "capture"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> CaptureEffectResult:
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
            self._handle_capture_failure(item, target)
            return {"success": False, "num_shakes": shakes, "extra": None}

        # Apply capture effects
        self._apply_capture_effects(item, target)

        return {"success": True, "num_shakes": shakes, "extra": None}

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
        tuxeball_modifier = prepare.TUXEBALL_MODIFIER

        # Type-based tuxeball
        if item.slug in [
            "tuxeball_earth",
            "tuxeball_fire",
            "tuxeball_metal",
            "tuxeball_water",
            "tuxeball_wood",
        ]:
            tuxeball_modifier = (
                0.2
                if target.types[0].slug != item.slug.replace("tuxeball_", "")
                else 1.5
            )

        # Flavored-based tuxeball
        if item.slug in [
            "tuxeball_hearty",
            "tuxeball_peppy",
            "tuxeball_refined",
            "tuxeball_salty",
            "tuxeball_zesty",
        ]:
            target.taste_warm = TasteWarm(item.slug.replace("tuxeball_", ""))

        # Gender-based tuxeball
        if item.slug in [
            "tuxeball_male",
            "tuxeball_female",
            "tuxeball_neuter",
        ]:
            tuxeball_modifier = (
                0.2
                if target.gender
                != GenderType(item.slug.replace("tuxeball_", ""))
                else 1.5
            )

        # Qiangong2 tuxeball ideas
        if item.slug == "tuxeball_ancient":
            tuxeball_modifier = 99.0
        elif item.slug == "tuxeball_crusher":
            crusher = ((target.armour / 5) * 0.01) + 1
            if crusher >= 1.4:
                crusher = 1.4
            if (
                self._calculate_status_modifier(target)
                == prepare.STATUS_POSITIVE
            ):
                crusher = 0.01
            tuxeball_modifier = crusher

        # Xero and Omni tuxeball ideas
        assert item.combat_state
        our_monster = item.combat_state.monsters_in_play[self.user][0]
        if our_monster:
            if item.slug == "tuxeball_xero":
                tuxeball_modifier = (
                    1.4
                    if our_monster.types[0].slug != target.types[0].slug
                    else 0.3
                )
            elif item.slug == "tuxeball_omni":
                tuxeball_modifier = (
                    0.3
                    if our_monster.types[0].slug != target.types[0].slug
                    else 1.4
                )

        # Lavish tuxeball idea
        if item.slug == "tuxeball_lavish":
            tuxeball_modifier = 1.5

        return tuxeball_modifier

    def _handle_capture_failure(self, item: Item, target: Monster) -> None:
        assert item.combat_state
        if item.slug == "tuxeball_park":
            empty = Technique()
            empty.load("empty")
            _wander = "spyder_park_wander"
            label = self.user.game_variables.get(item.slug, _wander)
            empty.use_tech = label
            item.combat_state._action_queue.rewrite(target, empty)

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        assert item.combat_state
        if item.slug == "tuxeball_candy":
            target.level += 1
        elif item.slug == "tuxeball_hardened":
            tuxeball = self.user.find_item(item.slug)
            if tuxeball:
                tuxeball.quantity -= 1

        if (
            target.slug in self.user.tuxepedia
            and self.user.tuxepedia[target.slug] == SeenStatus.seen
        ):
            item.combat_state._new_tuxepedia = True
        self.user.tuxepedia[target.slug] = SeenStatus.caught
        target.capture_device = item.slug
        target.wild = False
        self.user.add_monster(target, len(self.user.monsters))
