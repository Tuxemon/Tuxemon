# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.player_facing_npc import PlayerFacingNPCCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class ToTalkCondition(EventCondition):
    """
    Check if we are attempting to talk to an npc.

    Script usage:
        .. code-block::

            is to_talk <character>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").

    """

    name = "to_talk"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check if we are attempting to talk to an npc.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player attempts to talk with the npc.

        """
        player_next_to_and_facing_target = PlayerFacingNPCCondition().test(
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
        return player_next_to_and_facing_target and button_pressed
