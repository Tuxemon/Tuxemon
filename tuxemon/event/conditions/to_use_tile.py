# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.player_facing_tile import (
    PlayerFacingTileCondition,
)
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class ToUseTileCondition(EventCondition):
    """
    Check if we are attempting interact with a map condition tile.

    Script usage:
        .. code-block::

            is to_use_tile

    """

    name = "to_use_tile"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check if we are attempting interact with a map condition tile.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player attempts to interact with a map condition tile.

        """
        player_next_to_and_facing_tile = PlayerFacingTileCondition().test(
            session,
            condition,
        )
        button_pressed = ButtonPressedCondition().test(
            session,
            MapCondition(
                type="button_pressed",
                parameters=[
                    "K_RETURN",
                ],
                operator="is",
                width=0,
                height=0,
                x=0,
                y=0,
                name="",
            ),
        )
        return player_next_to_and_facing_tile and button_pressed
