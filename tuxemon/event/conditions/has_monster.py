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
