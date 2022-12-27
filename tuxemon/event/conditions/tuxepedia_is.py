# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import SeenStatus
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class TuxepediaIsCondition(EventCondition):
    """
    Check to see if the player has seen or caught a monster.

    Script usage:
        .. code-block::

            is tuxepedia_is <monster_slug>,<string>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").
        string: seen / caught

    """

    name = "tuxepedia_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has been seen or caught a monster.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has seen or caught a monster.

        """
        player = session.player

        # Read the parameters
        monster_key = condition.parameters[0]
        monster_str = condition.parameters[1]

        if monster_key in player.tuxepedia:
            if monster_str == "caught":
                if player.tuxepedia[monster_key] == SeenStatus.caught:
                    return True
            elif monster_str == "seen":
                if player.tuxepedia[monster_key] == SeenStatus.seen:
                    return True
                elif player.tuxepedia[monster_key] == SeenStatus.caught:
                    return True
            else:
                return False
