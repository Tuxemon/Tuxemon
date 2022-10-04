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

import random
from typing import NamedTuple

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class StatusEffectResult(TechEffectResult):
    pass


class StatusEffectParameters(NamedTuple):
    status: str


class StatusEffect(TechEffect[StatusEffectParameters]):
    """
    This effect has a chance to apply a status effect to a target monster.

    Parameters:
        slug: Name of the status effect.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "status"
    param_class = StatusEffectParameters

    def apply(self, user: Monster, target: Monster) -> StatusEffectResult:
        slug = self.parameters.status
        already_applied = any(t for t in target.status if t.slug == slug)
        success = (
            not already_applied
            and self.move.can_apply_status
            and self.move.potency >= random.random(),
        )
        tech = None
        if success:
            if slug == "status_faint":
                target.apply_status(Technique("status_faint"))
                return {"should_tackle": False}
            elif slug == "status_lifeleech":
                tech = Technique(slug, carrier=target, link=user)
                target.apply_status(tech)
            elif slug == "status_recover":
                tech = Technique(slug, link=user)
                target.apply_status(tech)
            else:
                tech = Technique(slug, carrier=target)
                target.apply_status(tech)

        return {"status": tech}
