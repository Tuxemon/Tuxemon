# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import BoundingBox, Operator, SpatialCondition
from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.char_facing_tile import CharFacingTileCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class ToUseTileCondition(EventCondition):
    """
    Check if we are attempting to interact with a map condition tile.

    Script usage:
        .. code-block::

            is to_use_tile
    """

    name = "to_use_tile"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        character_facing_tile = CharFacingTileCondition().test(
            session,
            condition,
        )
        box = BoundingBox(x=0, y=0, width=0, height=0)
        button_pressed = ButtonPressedCondition().test(
            session,
            SpatialCondition(
                type="button_pressed",
                parameters=[
                    "INTERACT",
                ],
                operator=Operator.IS,
                box=box,
                name="",
            ),
        )
        return character_facing_tile and button_pressed
