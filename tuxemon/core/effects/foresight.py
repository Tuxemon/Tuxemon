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
class ForesightEffect(CoreEffect):
    """
    Applies the "foresight" effect to a technique.

    This effect schedules the technique to be reused after a specified number
    of turns. The technique's power is set equal to the number of turns
    delayed, allowing it to be planned ahead for a guaranteed increase.

    **Parameters**

    - ``turn``: The number of turns after which the technique will be reused.

    **Example**

    .. code-block:: json

        "effects": [
            "foresight 3"
        ]
    """

    name = "foresight"
    turn: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if self.turn <= 0:
            raise ValueError(f"{self.turn} cannot be 0 or negative")

        combat_session = session.client.combat_session

        set_technique = Technique.create(tech.slug)
        set_technique.power = self.turn

        next_turn = combat_session.turn + self.turn
        action = EnqueuedAction(user, set_technique, target)
        combat_session.action_queue.add_pending(action, next_turn)

        return TechEffectResult(name=tech.name, success=True)
