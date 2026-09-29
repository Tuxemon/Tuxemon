# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@dataclass
class SwapEffect(CoreEffect):
    """
    Applies the "swap" effect to a technique.

    This effect changes the order of monsters in combat by swapping the
    user monster with the target monster. It is used exclusively in battle
    to reposition monsters within the party lineup.

    **Example**

    .. code-block:: json

        "effects": [
            "swap"
        ]
    """

    name = "swap"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        logger.debug(f"Swap: removing {user.name}, adding {target.name}")
        combat_session = session.client.combat_session
        combat_session.action_queue.swap(user, target)
        player = user.get_owner()
        event_bus = session.client.event_bus
        event_bus.publish("monster_swapped_out", monster=user)
        event_bus.publish(
            "monster_swapped_in", removed=user, added=target, player=player
        )
        return TechEffectResult(name=tech.name, success=True)
