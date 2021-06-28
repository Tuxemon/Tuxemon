#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#


import logging
import random

from math import sqrt

from tuxemon.item.itemeffect import ItemEffect


logger = logging.getLogger(__name__)


class CaptureEffect(ItemEffect):
    """Attempts to capture the target with 'power' capture strength."""

    name = "capture"
    valid_parameters = [(int, "power")]

    def apply(self, target):
        # Set up variables for capture equation
        status_modifier = 0

        # TODO: Item power is set to 1 in order to not effect the calculations
        # Research the proper item_powers of pokeballs to use it as a multiplier.
        item_power = 1
        # The number of shakes that a tuxemon can do to escape.
        total_shakes = 4
        # The max catch rate.
        max_catch_rate = 255
        # In every shake a random number form [0-65536] will be produced.
        max_shake_rate = 65536
        # Constant used in shake_check calculations
        shake_constant = 524325
        # Check if target has any status effects
        if not target.status == "Normal":
            status_modifier = 1.2

        # TODO: debug logging this info

        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        # Specifically the catch rate and the shake_check is based on the Generation III-IV
        # The rate of which a tuxemon is caught is approximetly catch_check/255

        catch_check = (
            (3 * target.hp - 2 * target.current_hp) * target.catch_rate * item_power * status_modifier / (3 * target.hp)
        )
        shake_check = shake_constant / (sqrt(sqrt(max_catch_rate / catch_check)) * 8)
        # Catch_resistance is a randomly generated number between the lower and upper catch_resistance of a tuxemon.
        # This value is used to slightly increase or decrease the chance of a tuxemon being caught. The value changes
        # Every time a new caprute device is thrown.
        catch_resistance = random.uniform(target.lower_catch_resistance, target.upper_catch_resistance)
        # Catch_resistance is applied to the shake_check
        shake_check = shake_check * catch_resistance
        
        # Debug section
        logger.debug("--- Capture Variables ---")
        logger.debug(
            "(3*target.hp - 2*target.current_hp) " "* target.catch_rate * item_power * status_modifier / (3*target.hp)"
        )

        msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"

        logger.debug(msg.format(target, item_power, status_modifier))
        logger.debug("shake_constant/(sqrt(sqrt(max_catch_rate/catch_check))*8)")
        logger.debug(f"524325/(sqrt(sqrt(255/{catch_check}))*8)")

        msg = "Each shake has a {}/65536 chance of breaking the creature free. (shake_check = {})"
        logger.debug(msg.format(round((shake_constant - shake_check) / shake_constant, 2), round(shake_check)))

        # 4 shakes to give monster chance to escape
        for i in range(0, total_shakes):
            random_num = random.randint(0, max_shake_rate)

            logger.debug(f"shake check {i}: random number {random_num}")
            if random_num > round(shake_check):
                return {"success": False, "capture": True, "num_shakes": i + 1}

        # add creature to the player's monster list
        self.user.add_monster(target)

        # TODO: remove monster from the other party
        return {"success": True, "capture": True, "num_shakes": 4}
