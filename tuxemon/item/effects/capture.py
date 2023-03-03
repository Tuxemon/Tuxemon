# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from math import sqrt
from typing import Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class CaptureEffectResult(ItemEffectResult):
    capture: bool
    num_shakes: int


@dataclass
class CaptureEffect(ItemEffect):
    """Attempts to capture the target."""

    name = "capture"
    tuxeball: Union[str, None] = None

    def apply(self, target: Monster) -> CaptureEffectResult:
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
        iid = self.user.game_variables["iid_fighting_monster"]
        fighting_monster = self.user.find_monster_by_id(iid)
        # Check type tuxeball and address malus/bonus
        tuxeball_modifier = 1.0
        if self.tuxeball is not None:
            # type based tuxeball
            if self.tuxeball == "tuxeball_earth":
                if target.type1 != "earth":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_fire":
                if target.type1 != "fire":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_metal":
                if target.type1 != "metal":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_water":
                if target.type1 != "water":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_wood":
                if target.type1 != "wood":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            # gender based tuxeball
            if self.tuxeball == "tuxeball_male":
                if target.gender != "male":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_female":
                if target.gender != "female":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            if self.tuxeball == "tuxeball_neuter":
                if target.gender != "neuter":
                    tuxeball_modifier = 0.2
                else:
                    tuxeball_modifier = 1.5
            # Qiangong2 tuxeball ideas
            if self.tuxeball == "tuxeball_ancient":
                tuxeball_modifier = 99
            if self.tuxeball == "tuxeball_crusher":
                crusher = ((target.armour / 5) * 0.01) + 1
                if crusher >= 1.4:
                    crusher = 1.4
                if status_category == "positive":
                    crusher = 0.01
                tuxeball_modifier = crusher
            if self.tuxeball == "tuxeball_xero":
                if fighting_monster.type1 != target.type1:
                    tuxeball_modifier = 1.4
                else:
                    tuxeball_modifier = 0.3
            if self.tuxeball == "tuxeball_omni":
                if fighting_monster.type1 != target.type1:
                    tuxeball_modifier = 0.3
                else:
                    tuxeball_modifier = 1.4
            # Sanglorian tuxeball ideas
            if self.tuxeball == "tuxeball_lavish":
                tuxeball_modifier = 1.5

        # TODO: debug logging this info
        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        # Specifically the catch rate and the shake_check is based on the Generation III-IV
        # The rate of which a tuxemon is caught is approximetly catch_check/255

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
        # Every time a new caprute device is thrown.
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
                # check for self.tuxeball
                if self.tuxeball is not None:
                    if self.tuxeball == "tuxeball_hardened":
                        tuxeball = self.user.find_item(self.tuxeball)
                        if tuxeball:
                            tuxeball.quantity += 1

                return {"success": False, "capture": True, "num_shakes": i + 1}

        if self.tuxeball is not None:
            # it increases the level +1 upon capture
            if self.tuxeball == "tuxeball_candy":
                capture_device = self.tuxeball
                target.level += 1
            else:
                capture_device = self.tuxeball

        # add creature to the player's monster list
        target.capture_device = capture_device
        self.user.add_monster(target)

        # TODO: remove monster from the other party
        return {"success": True, "capture": True, "num_shakes": 4}
