# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import TargetType
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)

@dataclass
class HealingEffect(CoreEffect):
    """
    Applies the "healing" effect to a technique.

    This effect restores HP to the user or its targets based on the
    technique's healing power. The healing amount is calculated using
    the same formula as the damage that would be dealt by a reliable
    technique of equal power.

    **Parameters**

    - ``objective``: Which targets to heal. When omitted, the technique's
      own target block is used (the same targets the other effects hit).
      Otherwise it may be any single target type, letting the heal target
      differently from the rest of the technique:

      - ``own_monster``: the monster using the technique
      - ``own_team``: the user's active team
      - ``own_trainer``: the user's whole party
      - ``enemy_monster``: the targeted monster
      - ``enemy_team``: the target's active team
      - ``enemy_trainer``: the target's whole party

    **Example**

    Heal whatever the technique targets:

    .. code-block:: json

        "effects": [
            "healing"
        ]

    Heal the user regardless of the technique's target block (e.g. a move
    that damages an enemy but heals the caster):

    .. code-block:: json

        "effects": [
            "healing own_monster"
        ]
    """

    name = "healing"
    objective: str = ""

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        targets: list[Monster] = []
        extra: list[str] = []
        done: bool = False

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            targets = self._resolve_targets(session, tech, user, target)

        if targets:
            for monster in targets:
                heal = formula.simple_heal(tech, monster)
                params = {"name": monster.name}
                if monster.hp_ratio < 1.0:
                    heal_amount = min(heal, monster.missing_hp)
                    monster.current_hp += heal_amount
                    done = True
                    extra.append(T.format("combat_state_healed", params))
                elif monster.hp_ratio == 1.0:
                    extra.append(T.format("combat_full_health", params))
        return TechEffectResult(name=tech.name, success=done, extras=extra)


    def _resolve_targets(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> list[Monster]:
        combat = session.client.combat_session
        if not self.objective:
            return combat.get_targets(tech, user, target)
        if self.objective not in {t.value for t in TargetType}:
            logger.error(
                f"{tech.name}: invalid healing objective '{self.objective}'"
            )
            return []
        return combat.get_targets_from_map(self.objective, user, target)
