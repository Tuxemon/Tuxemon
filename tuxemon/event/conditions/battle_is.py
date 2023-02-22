# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import OutputBattle
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class BattleIsCondition(EventCondition):
    """
    Check to see if the player has fought against NPC and won, lost or draw.

    Script usage:
        .. code-block::

            is battle_is <character>,<result>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").
        result: One among "won", "lost" or "draw"

    """

    name = "battle_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has fought against NPC and won, lost or draw.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has fought against a character or not.

        """
        player = session.player

        # Read the parameters
        character = condition.parameters[0]
        result = condition.parameters[1]

        outcomes = [otc.value for otc in OutputBattle]

        if player.battles:
            if result in outcomes:
                for battle in player.battles:
                    if (
                        battle.opponent == character
                        and battle.outcome == result
                    ):
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False
