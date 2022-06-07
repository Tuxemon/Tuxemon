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

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class EvolveMonstersCondition(EventCondition):
    """
    Check to see if monsters can be evolved on a evolutionary path.

    Script usage:
        .. code-block::

            is evolve_monsters <evolution>

    Script parameters:
        evolution: Name of a monster evolution.

    """

    name = "evolve_monsters"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a monster can be evolved on a evolutionary path.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether a monster in the player party can evolve to the
            specified evolution.

        """
        player = session.player
        for monster in player.monsters:
            new_slug = monster.get_evolution(condition.parameters[0])
            if new_slug:
                return True
        return False
