# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class HasMonsterCondition(EventCondition):
    """
    Check to see the player is has a monster in his party.

    Script usage:
        .. code-block::

            is has_monster <monster>

    Script parameters:
        monster: Monster slug name (e.g. "rockitten").

    """

    name = "has_monster"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see the player is has a monster in his party.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has the monster in his party.

        """
        player = session.player
        monster_slug = condition.parameters[0]
        if player.find_monster(monster_slug) is None:
            return False
        else:
            return True
