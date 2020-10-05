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

from tuxemon.core.event.eventcondition import EventCondition


class MonsterPropertyCondition(EventCondition):
    """ Checks to see if a monster property or condition is as asked
    """
    name = "monster_property"

    def test(self, session,  condition):
        """Checks to see if a monster property or condition is as asked

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        """
        slot = condition.parameters[0]
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
