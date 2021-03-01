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

from tuxemon.core.item.itemeffect import ItemEffect

logger = logging.getLogger(__name__)


class CaptureEffect(ItemEffect):
    """Attempts to capture the target with 'power' capture strength.
    """
    name = "capture"
    valid_parameters = [
        (int, "power")
    ]

    def apply(self, target):
        # Set up variables for capture equation
        status_modifier = 0
        item_power = self.parameters.power

        # Check if target has any status effects
        if not target.status == "Normal":
            status_modifier = 1.5

        # TODO: debug logging this info

        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        catch_check = (3 * target.hp - 2 * target.current_hp) \
            * target.catch_rate * item_power * status_modifier / (3 * target.hp)
        shake_check = 65536 / (255 / catch_check) ** 0.1875

        logger.debug("--- Capture Variables ---")
        logger.debug("(3*target.hp - 2*target.current_hp) "
                     "* target.catch_rate * item_power * status_modifier / (3*target.hp)")

        msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"
        logger.debug(msg.format(target, item_power, status_modifier))

        logger.debug("65536 / (255 / catch_check) ** 0.1875")
        logger.debug("65536 / (255 / {}) ** 0.1875".format(catch_check))

        msg = "Each shake has a {} chance of breaking the creature free. (shake_check = {})"
        logger.debug(msg.format(round((65536 - shake_check) / 65536, 2), round(shake_check)))

        # 4 shakes to give monster chance to escape
        for i in range(0, 4):
            random_num = random.randint(0, 65536)
            logger.debug("shake check {}: random number {}".format(i, random_num))
            if random_num > round(shake_check):
                return {"success": False,
                        "capture": True,
                        "num_shakes": i + 1}

        # add creature to the player's monster list
        self.user.add_monster(target)

        # TODO: remove monster from the other party
        return {"success": True,
                "capture": True,
                "num_shakes": 4}
