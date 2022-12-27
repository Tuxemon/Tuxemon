# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PlayerDefeatedCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon, and all tuxemon in their
    party are defeated.

    Script usage:
        .. code-block::

            is player_defeated

    """

    name = "player_defeated"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see the player has at least one tuxemon, and all tuxemon in their
        party are defeated.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has at least one tuxemon in their party and if
            all their tuxemon are defeated.

        """
        player = session.player

        if player.monsters:
            for mon in player.monsters:
                if not "status_faint" in (s.slug for s in mon.status):
                    return False

            return True
        return False
