# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass
from math import sqrt
from typing import TYPE_CHECKING, Union

from tuxemon.db import ElementType, GenderType, TasteWarm
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
        combat_state = item.combat_state
        capture_device = "tuxeball"
        # The number of shakes that a tuxemon can do to escape.
        total_shakes = 4
        # The max catch rate.
        max_catch_rate = 255
        # In every shake a random number form [0-65536] will be produced.
        max_shake_rate = 65536
        # Constant used in shake_check calculations
        shake_constant = 524325
        # Check if target has status/condition:
        status_modifier = 1.0
        status_category = ""
        if target.status:
            for status in target.status:
                if status.category == "negative":
                    status_category = "negative"
                    status_modifier = 1.2
                if status.category == "positive":
                    status_category = "positive"
        # retrieves monster fighting (player)
        iid = uuid.UUID(self.user.game_variables["iid_fighting_monster"])
        fighting_monster = self.user.find_monster_by_id(iid)
        # Check type tuxeball and address malus/bonus
        tuxeball_modifier = 1.0
        # type based tuxeball
        if item.slug == "tuxeball_earth":
            if target.types[0].slug != ElementType.earth:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_fire":
            if target.types[0].slug != ElementType.fire:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_metal":
            if target.types[0].slug != ElementType.metal:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_water":
            if target.types[0].slug != ElementType.water:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_wood":
            if target.types[0].slug != ElementType.wood:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
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
            if target.gender != GenderType.male:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_female":
            if target.gender != GenderType.female:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        if item.slug == "tuxeball_neuter":
            if target.gender != GenderType.neuter:
                tuxeball_modifier = 0.2
            else:
                tuxeball_modifier = 1.5
        # Qiangong2 tuxeball ideas
        if item.slug == "tuxeball_ancient":
            tuxeball_modifier = 99
        if item.slug == "tuxeball_crusher":
            crusher = ((target.armour / 5) * 0.01) + 1
            if crusher >= 1.4:
                crusher = 1.4
            if status_category == "positive":
                crusher = 0.01
            tuxeball_modifier = crusher
        if fighting_monster:
            if item.slug == "tuxeball_xero":
                if fighting_monster.types[0].slug != target.types[0].slug:
                    tuxeball_modifier = 1.4
                else:
                    tuxeball_modifier = 0.3
            if item.slug == "tuxeball_omni":
                if fighting_monster.types[0].slug != target.types[0].slug:
                    tuxeball_modifier = 0.3
                else:
                    tuxeball_modifier = 1.4
            # Sanglorian tuxeball ideas
            if item.slug == "tuxeball_lavish":
                tuxeball_modifier = 1.5

        # TODO: debug logging this info
        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        # Specifically the catch rate and the shake_check is based on the Generation III-IV
        # The rate of which a tuxemon is caught is approximately catch_check/255

        catch_check = (
            (3 * target.hp - 2 * target.current_hp)
            * target.catch_rate
            * status_modifier
            * tuxeball_modifier
            / (3 * target.hp)
        )
        shake_check = shake_constant / (
            sqrt(sqrt(max_catch_rate / catch_check)) * 8
        )
        # Catch_resistance is a randomly generated number between the lower and upper catch_resistance of a tuxemon.
        # This value is used to slightly increase or decrease the chance of a tuxemon being caught. The value changes
        # Every time a new capture device is thrown.
        catch_resistance = random.uniform(
            target.lower_catch_resistance, target.upper_catch_resistance
        )
        # Catch_resistance is applied to the shake_check
        shake_check = shake_check * catch_resistance

        # Debug section
        logger.debug("--- Capture Variables ---")
        logger.debug(
            "(3*target.hp - 2*target.current_hp) "
            "* target.catch_rate * status_modifier * tuxeball_modifier / (3*target.hp)"
        )

        msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"

        logger.debug(msg.format(target, status_modifier, tuxeball_modifier))
        logger.debug(
            "shake_constant/(sqrt(sqrt(max_catch_rate/catch_check))*8)"
        )
        logger.debug(f"524325/(sqrt(sqrt(255/{catch_check}))*8)")

        msg = "Each shake has a {}/65536 chance of breaking the creature free. (shake_check = {})"
        logger.debug(
            msg.format(
                round((shake_constant - shake_check) / shake_constant, 2),
                round(shake_check),
            )
        )

        # 4 shakes to give monster chance to escape
        for i in range(0, total_shakes):
            random_num = random.randint(0, max_shake_rate)
            logger.debug(f"shake check {i}: random number {random_num}")
            if random_num > round(shake_check):
                if item.slug == "tuxeball_hardened":
                    tuxeball = self.user.find_item(item.slug)
                    if tuxeball:
                        tuxeball.quantity += 1

                # escape monster
                if random.randint(0, 100) <= target.escape_rate:
                    esc = Technique()
                    esc.load("menu_run")
                    if combat_state and fighting_monster:
                        esc.combat_state = combat_state
                        combat_state.rewrite_action_queue(
                            target, fighting_monster, esc
                        )
                return {"success": False, "num_shakes": i + 1, "extra": None}

        # it increases the level +1 upon capture
        if item.slug == "tuxeball_candy":
            capture_device = item.slug
            target.level += 1
        else:
            capture_device = item.slug

        # add creature to the player's monster list
        target.capture_device = capture_device
        self.user.add_monster(target, len(self.user.monsters))

        # TODO: remove monster from the other party
        return {"success": True, "num_shakes": 4, "extra": None}
