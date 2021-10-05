#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.event import MapCondition


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
