# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import BlockedReason
from tuxemon.locale.locale import T
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class GiveEffect(CoreEffect):
    """
    Gives a status to a monster.

    This effect attempts to apply a status condition to one or more target
    monsters. The chance of success depends on the technique's potency and
    accuracy compared against random rolls. Targets may resist the effect if
    immune due to items.

    **Parameters**

    - ``condition``: The status slug to apply (e.g. ``enraged``).
    - ``objectives``: Colon-separated list of target groups (e.g.
      ``enemy_monster`` or ``enemy_monster:own_monster``).

    **Example**

    .. code-block:: json

        "effects": [
            "give enraged enemy_monster"
        ]
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
        protected_info = []
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
                logger.info(
                    f"[COMBAT] give {self.condition} -> {monster.name} (via {tech.name})"
                )
            elif result.blocked_reason == BlockedReason.IMMUNE_BY_ITEM:
                immune_info.append(f"{monster.name} ({result.blocked_by})")
            elif result.blocked_by and result.blocked_reason not in (
                BlockedReason.IMMUNE_BY_ITEM,
            ):
                protected_info.append((monster.name, result.blocked_by, status.name))

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

        for monster_name, protecting_status, condition_name in protected_info:
            params = {
                "method": protecting_status,
                "target": monster_name,
                "condition": condition_name,
            }
            extras.append(T.format("combat_state_prevented", params))

        if successful_targets:
            event_bus = session.client.event_bus
            event_bus.publish("status_applied")
            event_bus.publish("update_party_hud")

        return TechEffectResult(
            name=tech.name, success=bool(monsters), extras=extras
        )
