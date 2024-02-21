# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import formula, prepare
from tuxemon.db import CategoryCondition as Category
from tuxemon.db import ElementType, GenderType, SeenStatus, TasteWarm
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
        assert target and item.combat_state
        # Check if target has status/condition:
        status_modifier = prepare.STATUS_MODIFIER
        status_category = ""
        if target.status and target.status[0].category:
            status_modifier = (
                prepare.STATUS_NEGATIVE
                if target.status[0].category == Category.negative
                else prepare.STATUS_POSITIVE
            )
            status_category = (
                Category.negative
                if target.status[0].category == Category.negative
                else Category.positive
            )
        # Check type tuxeball and address malus/bonus
        tuxeball_modifier = prepare.TUXEBALL_MODIFIER
        # type based tuxeball
        if item.slug == "tuxeball_earth":
            tuxeball_modifier = (
                0.2 if target.types[0].slug != ElementType.earth else 1.5
            )
        if item.slug == "tuxeball_fire":
            tuxeball_modifier = (
                0.2 if target.types[0].slug != ElementType.fire else 1.5
            )
        if item.slug == "tuxeball_metal":
            tuxeball_modifier = (
                0.2 if target.types[0].slug != ElementType.metal else 1.5
            )
        if item.slug == "tuxeball_water":
            tuxeball_modifier = (
                0.2 if target.types[0].slug != ElementType.water else 1.5
            )
        if item.slug == "tuxeball_wood":
            tuxeball_modifier = (
                0.2 if target.types[0].slug != ElementType.wood else 1.5
            )
        # flavoured based tuxeball
        if item.slug == "tuxeball_hearty":
            target.taste_warm = TasteWarm.hearty
        if item.slug == "tuxeball_peppy":
            target.taste_warm = TasteWarm.peppy
        if item.slug == "tuxeball_refined":
            target.taste_warm = TasteWarm.refined
        if item.slug == "tuxeball_salty":
            target.taste_warm = TasteWarm.salty
        if item.slug == "tuxeball_zesty":
            target.taste_warm = TasteWarm.zesty
        # gender based tuxeball
        if item.slug == "tuxeball_male":
            tuxeball_modifier = (
                0.2 if target.gender != GenderType.male else 1.5
            )
        if item.slug == "tuxeball_female":
            tuxeball_modifier = (
                0.2 if target.gender != GenderType.female else 1.5
            )
        if item.slug == "tuxeball_neuter":
            tuxeball_modifier = (
                0.2 if target.gender != GenderType.neuter else 1.5
            )
        # Qiangong2 tuxeball ideas
        if item.slug == "tuxeball_ancient":
            tuxeball_modifier = 99.0
        if item.slug == "tuxeball_crusher":
            crusher = ((target.armour / 5) * 0.01) + 1
            if crusher >= 1.4:
                crusher = 1.4
            if status_category == Category.positive:
                crusher = 0.01
            tuxeball_modifier = crusher
        # retrieves monster fighting (player)
        our_monster = item.combat_state.monsters_in_play[self.user][0]
        if our_monster and item.slug == "tuxeball_xero":
            tuxeball_modifier = (
                1.4
                if our_monster.types[0].slug != target.types[0].slug
                else 0.3
            )
        if our_monster and item.slug == "tuxeball_omni":
            tuxeball_modifier = (
                0.3
                if our_monster.types[0].slug != target.types[0].slug
                else 1.4
            )

        # Sanglorian tuxeball ideas
        if item.slug == "tuxeball_lavish":
            tuxeball_modifier = 1.5

        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            if item.slug == "tuxeball_hardened":
                tuxeball = self.user.find_item(item.slug)
                if tuxeball:
                    tuxeball.quantity += 1
            if item.slug == "tuxeball_park":
                empty = Technique()
                empty.load("empty")
                _wander = "spyder_park_wander"
                label = self.user.game_variables.get(item.slug, _wander)
                empty.use_tech = label
                item.combat_state.rewrite_action_queue_method(target, empty)

            return {"success": False, "num_shakes": shakes, "extra": None}

        # it increases the level +1 upon capture
        if item.slug == "tuxeball_candy":
            target.level += 1

        if (
            target.slug in self.user.tuxepedia
            and self.user.tuxepedia[target.slug] == SeenStatus.seen
        ):
            item.combat_state._new_tuxepedia = True
        self.user.tuxepedia[target.slug] = SeenStatus.caught
        target.capture_device = item.slug
        target.wild = False
        # add creature to the player's monster list
        self.user.add_monster(target, len(self.user.monsters))

        # TODO: remove monster from the other party
        return {"success": True, "num_shakes": shakes, "extra": None}
