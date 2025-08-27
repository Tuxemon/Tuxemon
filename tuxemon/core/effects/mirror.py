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
class MirrorEffect(CoreEffect):
    """
    A mirror effect that switches the user and target sprites.

    The direction of the mirror effect can be specified using the `direction` parameter,
    which can be one of the following:
    - `both`: Switch both the user and target sprites.
    - `user_to_target`: Switch the user sprite to face the target.
    - `target_to_user`: Switch the target sprite to face the user.
    """

    name = "mirror"
    direction: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        event_bus = session.client.event_bus
        event_bus.publish(
            "mirror_effect", user=user, target=target, direction=self.direction
        )
        return TechEffectResult(name=tech.name, success=True)
