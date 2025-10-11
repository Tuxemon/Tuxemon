# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import CategoryStatus

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class RemoveEffect(CoreEffect):
    """
    This effect has a chance to remove a status effect.

    Parameters:
        status: The Status slug (e.g. enraged) or 'positive', 'negative', 'all'.
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "remove xxx,own_monster" removes only xxx
    eg "remove all,own_monster" removes everything
    """

    name = "remove"
    status: str
    objectives: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters: list[Monster] = []

        objectives = self.objectives.split(":")
        potency = random.random()
        value = session.client.combat_session.get_tech_hit(user)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            monsters = session.client.combat_session.get_target_monsters(
                objectives, user, target
            )
            for monster in monsters:
                current_status = monster.status.get_current_status()
                if self.status == "all":
                    monster.status.clear_status(session)
                elif (
                    self.status in ("positive", "negative")
                    and current_status
                    and current_status.category
                ):
                    if (
                        self.status == "positive"
                        and current_status.category == CategoryStatus.positive
                    ):
                        monster.status.remove_status()
                    elif (
                        self.status == "negative"
                        and current_status.category == CategoryStatus.negative
                    ):
                        monster.status.remove_status()
                elif current_status and self.status == current_status.slug:
                    monster.status.remove_status()

        if monsters:
            event_bus = session.client.event_bus
            event_bus.publish("status_applied")
            event_bus.publish("update_party_hud")

        return TechEffectResult(name=tech.name, success=bool(monsters))
