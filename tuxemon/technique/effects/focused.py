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

import logging
from typing import NamedTuple, Optional

from tuxemon.combat import check_status
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


class FocusedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class FocusedEffectParameters(NamedTuple):
    objective: str


class FocusedEffect(TechEffect[FocusedEffectParameters]):
    """
    This effect has a chance to apply the focused status effect.
    """

    name = "focused"
    param_class = FocusedEffectParameters

    def apply(self, user: Monster, target: Monster) -> FocusedEffectResult:
        if self.parameters.objective == "user" and self.user is None:
            already_applied = check_status(user, "status_focused")
        elif self.parameters.objective == "target":
            already_applied = check_status(target, "status_focused")
        else:
            already_applied = check_status(self.user, "status_focused")
        if not already_applied:
            tech = Technique("status_focused", link=user)
            if self.parameters.objective == "user":
                user.apply_status(tech)
            elif self.parameters.objective == "target":
                target.apply_status(tech)
            return {"status": tech}

        if already_applied:
            return {"damage": 0, "should_tackle": False, "success": False}
