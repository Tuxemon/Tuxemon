# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import Operator, SpatialCondition
from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.char_at import CharAtCondition
from tuxemon.event.conditions.char_facing import CharFacingCondition
from tuxemon.event.conditions.char_facing_char import CharFacingCharCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class BehaviorCondition(EventCondition):
    """
    Check if the behavior's conditions are true.

    Behavior is a combination of actions and conditions.

    """

    name = "behav"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        param = condition.parameters
        if param[0] == "talk":
            char_facing_char = CharFacingCharCondition().test(
                session,
                SpatialCondition(
                    type="char_facing_char",
                    parameters=["player", param[1]],
                    box=condition.box,
                    operator=Operator.IS,
                    name="cond10",
                ),
            )
            button_pressed = ButtonPressedCondition().test(
                session,
                SpatialCondition(
                    type="button_pressed",
                    parameters=["INTERACT"],
                    box=condition.box,
                    operator=Operator.IS,
                    name="cond20",
                ),
            )
            return char_facing_char and button_pressed

        elif param[0] == "door":
            facing = param[1]
            char_at = CharAtCondition().test(
                session,
                SpatialCondition(
                    type="char_at",
                    parameters=["player"],
                    box=condition.box,
                    operator=Operator.IS,
                    name="cond10",
                ),
            )
            char_facing = CharFacingCondition().test(
                session,
                SpatialCondition(
                    type="char_facing",
                    parameters=["player", facing],
                    box=condition.box,
                    operator=Operator.IS,
                    name="cond20",
                ),
            )
            return char_at and char_facing

        return False
