# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique

# damage each enemy takes when more than one of them is hit at once
MULTI_TARGET_MODIFIER = 0.75

@dataclass
class DamageEffect(CoreEffect):
    """
    Applies damage to one or more target monsters.

    This effect is triggered when ``damage`` is defined in a technique's
    effect list. It calculates damage based on the technique, user, and
    target, then reduces the target's HP accordingly.

    **Example**

    .. code-block:: json

        "effects": [
            "damage"
        ]
    """

    name = "damage"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        damage = 0
        mult = 1.0
        targets: list[Monster] = []
        enemy_side: Sequence[Monster] = []

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            targets = session.client.combat_session.get_targets(
                tech, user, target
            )
            enemy_side = session.client.combat_session.get_own_monsters(target)

        spread = sum(1 for m in targets if m in enemy_side) > 1

        for monster in targets:
            dmg, m = formula.simple_damage_calculate(tech, user, monster)
            if spread and monster in enemy_side:
                dmg = int(dmg * MULTI_TARGET_MODIFIER)
            monster.current_hp = max(0, monster.current_hp - dmg)
            if monster == target:
                damage, mult = dmg, m
            else:
                # to avoid double registration in the self._damage_map
                session.client.combat_session.enqueue_damage(
                    user, monster, dmg
                )

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            element_multiplier=mult,
            should_tackle=bool(damage),
            success=bool(damage),
        )
