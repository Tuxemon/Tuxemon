# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.action_queue import EnqueuedAction
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.event import get_event_bus
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class DisappearEffect(CoreEffect):
    """
    Tuxemon disappears. It's followed by "appear".

    Parameters:
        attack: slug technique (attack when lands).
    """

    name = "disappear"
    attack: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat_session = session.client.combat_session
        get_event_bus().publish("monster_disappeared", user=user)
        user.out_of_range = True
        land_technique = Technique.create(self.attack)
        land_action = EnqueuedAction(user, land_technique, target)
        turn = combat_session.turn
        combat_session.action_queue.add_pending(land_action, turn)
        return TechEffectResult(name=tech.name, success=True)
