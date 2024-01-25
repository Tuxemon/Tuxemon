# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class MonsterFlairCondition(EventCondition):
    """
    Check to see if the given monster flair matches the expected value.

    Script usage:
        .. code-block::

            is monster_flair <slot>,<category>,<name>

    Script parameters:
        slot: Position of the monster in the player monster list.
        category: Category of the flair.
        name: Name of the flair.

    """

    name = "monster_flair"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the given monster flair matches the expected value.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the monster flair matches the expected value.

        """
        slot = int(condition.parameters[0])
        category = condition.parameters[1]
        name = condition.parameters[2]

        monster = session.player.monsters[slot]
        try:
            return monster.flairs[category].name == name
        except KeyError:
            return False
        return False
