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

from __future__ import annotations
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from typing import NamedTuple, Union
from tuxemon.monster import Monster


class ReviveEffectResult(ItemEffectResult):
    pass


class ReviveEffectParameters(NamedTuple):
    pass


class ReviveEffect(ItemEffect[ReviveEffectParameters]):
    """
    Revives the target tuxemon, and sets HP to 1.
    """

    name = "revive"
    param_class = ReviveEffectParameters

    def apply(self, target: Monster) -> ReviveEffectResult(ItemEffectResult):
        target.status = []
        target.current_hp = 1

        return {"success": True}
