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
# Adam Chevalier <chevalieradam2@gmail.com>
#

from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class EvolveEffectResult(ItemEffectResult):
    pass


@dataclass
class EvolveEffect(ItemEffect):
    """This effect evolves the target into the monster in the parameters."""

    name = "evolve"
    monster_evolve: str

    def apply(self, target: Monster) -> EvolveEffectResult:
        if self.monster_evolve == "random":
            choices = [d for d in target.evolutions if d.path == "item"]
            evolution = random.choice(choices).monster_slug
            self.user.evolve_monster(target, evolution)
            return {"success": True}
        else:
            for evolution in target.evolutions:
                if evolution.monster_slug == self.monster_evolve:
                    self.user.evolve_monster(target, self.monster_evolve)
                    return {"success": True}
                else:
                    return {"success": False}
