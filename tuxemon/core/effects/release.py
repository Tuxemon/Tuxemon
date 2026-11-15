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
class ReleaseEffect(CoreEffect):
    """
    Executes the second turn of a two-turn charging technique. This effect
    performs the stored attack after the charging phase has completed and
    clears the monster's charging state. It is typically paired with a
    corresponding charge effect to form a complete multi-turn move.

    **Parameters**

    This effect takes no parameters. It simply resolves the charged attack
    when the monster is in a charging state.

    **Example**

    .. code-block:: json

        "effects": [
            "release"
        ]
    """

    name = "release"

    def should_run_tech(
        self,
        session: Session,
        tech: Technique,
        user: Monster | None,
        target: Monster | None,
    ) -> bool:
        if user is None:
            return False
        return user.is_charging

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not user.is_charging:
            return TechEffectResult(name=tech.name, success=False)

        user.is_charging = False
        user.charged_technique = None
        return TechEffectResult(name=tech.name, success=True)
