# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.action_queue import EnqueuedAction
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class ChargeEffect(CoreEffect):
    """
    Handles the first turn of a two-turn charging technique. This effect marks
    the monster as charging and schedules the corresponding release technique
    to execute on the following turn. It is typically paired with a
    ``release`` effect to complete the multi-turn sequence.

    **Parameters**

    This effect takes no parameters. It simply initiates the charging state
    and queues the release action for the next turn.

    **Example**

    .. code-block:: json

        "effects": [
            "charge"
        ]
    """

    name = "charge"

    def should_run_tech(
        self,
        session: Session,
        tech: Technique,
        user: Monster | None,
        target: Monster | None,
    ) -> bool:
        if user is None:
            return False
        return not user.is_charging

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat_session = session.client.combat_session
        queue = combat_session.action_queue
        user.is_charging = True
        user.charged_technique = tech.slug
        release_tech = Technique.create(tech.slug)
        release_action = EnqueuedAction(user, release_tech, target)
        queue.schedule_action_in_turns(release_action, 1)
        return TechEffectResult(name=tech.name, success=True)
