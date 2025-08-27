# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class AppearEffect(CoreEffect):
    """
    Tuxemon re-appears, it follows "disappear".

    """

    name = "appear"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        if user.out_of_range:
            user.out_of_range = False
            event_bus = session.client.event_bus
            event_bus.publish("monster_appeared", user=user)

        target_is_out_of_range = target.out_of_range

        return TechEffectResult(
            name=tech.name,
            success=not target_is_out_of_range,
            should_tackle=not target_is_out_of_range,
        )
