# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.action_queue import EnqueuedAction
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class LockedMoveEffect(CoreEffect):
    """
    Forces a monster to repeat the same technique for a fixed number of turns.
    During this locked sequence, the monster cannot choose another move. Once
    the sequence ends, the monster may become confused based on a configurable
    probability.

    **Parameters**

    - ``turns``: The number of consecutive turns the monster is forced to repeat
      the same technique. Must be a positive integer.
    - ``confuse_chance``: A floating-point value between ``0`` and ``1`` that
      determines the probability of the monster becoming confused after the
      locked sequence ends.

    **Example**

    .. code-block:: json

        "effects": [
            "locked 2 0.33"
        ]
    """

    name = "locked"
    turns: int = 2
    confuse_chance: float = 0.33

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        combat_session = session.client.combat_session
        queue = combat_session.action_queue
        user.locked_turns_left = self.turns
        user.locked_move = tech.slug
        user.locked_turns_left -= 1

        # Schedule next forced use
        if user.locked_turns_left > 0:
            next_tech = Technique.create(user.locked_move)
            next_action = EnqueuedAction(user, next_tech, target)
            queue.schedule_action_in_turns(next_action, 1)

        # End of lock: apply confusion
        else:
            user.locked_turns_left = 0
            user.locked_move = None

            if random.random() < self.confuse_chance:
                status = Status.create("confused", target, target.steps)
                result = target.status.apply_status(session, status)
                if result.applied:
                    event_bus = session.client.event_bus
                    event_bus.publish("status_applied")
                    event_bus.publish("update_party_hud")

        return TechEffectResult(name=tech.name, success=True)
