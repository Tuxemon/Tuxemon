# -*- coding: utf-8 -*-
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


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class EventCondition(object):
    """

    """
    name = "GenericCondition"

    def __init__(self):
        pass

    def test(self, game, condition):
        """ Return True if satisfied, or False if not

        :param game:
        :param condition:
        :rtype: bool
        """
        pass

    def get_persist(self, game):
        """ Return dictionary for this event class's data

        * This dictionary will be shared across all conditions
        * This dictionary will be saved when game is saved

        :return:
        """
        # Create a dictionary that will track movement

        try:
            return game.event_persist[self.name]
        except KeyError:
            persist = dict()
            game.event_persist[self.name] = persist
            return persist

    @property
    def done(self):
        return True
