#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#




class EventCondition:
    """

    """
    name = "GenericCondition"

    def __init__(self):
        pass

    def test(self, session, condition):
        """ Return True if satisfied, or False if not

        :param tuxemon.core.session.Session session:
        :param Dict condition:
        :rtype: bool
        """
        pass

    def get_persist(self, session):
        """ Return dictionary for this event class's data

        * This dictionary will be shared across all conditions
        * This dictionary will be saved when game is saved

        :return:
        """
        # Create a dictionary that will track movement

        try:
            return session.client.event_persist[self.name]
        except KeyError:
            persist = dict()
            session.client.event_persist[self.name] = persist
            return persist

    @property
    def done(self):
        return True
