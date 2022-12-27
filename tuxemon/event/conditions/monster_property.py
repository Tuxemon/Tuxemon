# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class MonsterPropertyCondition(EventCondition):
    """
    Check to see if a monster property or condition is as asked.

    Script usage:
        .. code-block::

            is monster_property <slot>,<property>,<value>

    Script parameters:
        slot: Position of the monster in the player monster list.
        property: Property of the monster to check (e.g. "level"). Valid values
            are:
                - name
                - level
                - level_reached
                - type
                - category
                - shape
        value: Value to compare the property with.

    """

    name = "monster_property"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """Check to see if a monster property or condition is as asked

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the monster property is verified.

        """
        slot = int(condition.parameters[0])
        prop = condition.parameters[1]
        val = condition.parameters[2]

        if int(slot) >= len(session.player.monsters):
            return False

        monster = session.player.monsters[slot]
        if prop == "name":
            return monster.name == val
        elif prop == "level":
            return str(monster.level) == val
        elif prop == "level_reached":
            return monster.level >= int(val)
        elif prop == "type":
            return monster.slug == val
        elif prop == "category":
            return monster.category == val
        elif prop == "shape":
            return monster.shape == val
        else:
            return False
