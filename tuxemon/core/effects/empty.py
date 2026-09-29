# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class EmptyEffect(CoreEffect):
    """
    Applies the "empty" effect to a technique.

    This effect allows a technique to display its animation without failing,
    even if the effect list is empty. Normally, a technique with no effects
    would automatically fail because success defaults to ``False``.

    **Example**

    .. code-block:: json

        "effects": [
            "empty"
        ]
    """

    name = "empty"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        return TechEffectResult(name=tech.name, success=tech.hit)
