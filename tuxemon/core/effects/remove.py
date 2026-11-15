# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import CategoryStatus

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class RemoveEffect(CoreEffect):
    """
    Applies the "remove" effect to a technique.

    This effect attempts to remove one or more status effects from the
    specified targets. The status to be removed can be a specific slug
    (e.g., ``enraged``), or a category such as ``positive``, ``negative``,
    or ``all``.

    **Parameters**

    - ``status``: Determines which status effect(s) to remove.
      - Specific slug (e.g., ``enraged``): Removes only that status.
      - ``positive``: Removes only positive status effects.
      - ``negative``: Removes only negative status effects.
      - ``all``: Removes all status effects.
    - ``objectives``: Colon-separated string specifying which monsters are
      affected. Examples:
      - ``own_monster`` → removes statuses from the user.
      - ``enemy_monster`` → removes statuses from the target.
      - ``enemy_monster:own_monster`` → removes statuses from both.

    **Example**

    .. code-block:: json

        "effects": [
            "remove all own_monster"
        ]
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
                current_status = monster.status.current_status
                if self.status == "all":
                    monster.status.clear_status(session)
                elif (
                    self.status in ("positive", "negative")
                    and current_status
                    and current_status.category
                ):
                    if (
                        self.status == "positive"
                        and current_status.category == CategoryStatus.POSITIVE
                    ):
                        monster.status.clear_status(session)
                    elif (
                        self.status == "negative"
                        and current_status.category == CategoryStatus.NEGATIVE
                    ):
                        monster.status.clear_status(session)
                elif current_status and self.status == current_status.slug:
                    monster.status.clear_status(session)

        if monsters:
            event_bus = session.client.event_bus
            event_bus.publish("status_applied")
            event_bus.publish("update_party_hud")

        return TechEffectResult(name=tech.name, success=bool(monsters))
