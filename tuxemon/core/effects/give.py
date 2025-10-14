# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale import T
from tuxemon.monster_dir.status import BlockedReason
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class GiveEffect(CoreEffect):
    """
    This effect has a chance to give a status effect.

    Parameters:
        condition: The Status slug (e.g. enraged).
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "give enraged,own_monster"
    """

    name = "give"
    condition: str
    objectives: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        objectives = self.objectives.split(":")
        potency = random.random()
        hit = session.client.combat_session.get_tech_hit(user)
        success = tech.potency >= potency and tech.accuracy >= hit

        if not success:
            return TechEffectResult(name=tech.name)

        immune_info = []
        successful_targets = []
        extras = []
        monsters = session.client.combat_session.get_target_monsters(
            objectives, user, target
        )

        for monster in monsters:
            status = Status.create(self.condition, monster, monster.steps)
            if status.bond:
                status.set_linked_monster(user)
            result = monster.status.apply_status(session, status)
            if result.applied:
                successful_targets.append(monster)
            elif result.blocked_reason == BlockedReason.IMMUNE_BY_ITEM:
                immune_info.append(f"{monster.name} ({result.blocked_by})")

        if immune_info:
            immune_names = ", ".join(immune_info)
            key = (
                "combat_state_immune"
                if len(immune_info) == 1
                else "combat_state_immune_multiple"
            )
            params = {"target": immune_names, "method": status.name}
            extract_text = T.format(key, params)
            extras = [extract_text]

        if successful_targets:
            event_bus = session.client.event_bus
            event_bus.publish("status_applied")
            event_bus.publish("update_party_hud")

        return TechEffectResult(
            name=tech.name, success=bool(monsters), extras=extras
        )
