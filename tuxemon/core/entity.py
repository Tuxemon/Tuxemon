# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
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
# Leif Theden <leif.theden@gmail.com>
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.world import WorldBody


class Entity(object):
    """ Eventually a class for all things that exist on the
        game map, like NPCs, players, objects, etc

        Need to refactor in most NPC code to here.
        Need to refactor -out- all drawing/sprite code.
        Consider to refactor out world position/movement into "Body" class
    """

    def __init__(self):
        self.slug = None
        self.world = None
        self.instance_id = None
        self.body = WorldBody()

    def get_state(self, session):
        """ Get Entities internal state for saving/loading
        
        :param tuxemon.core.session.Session session:
        :rtype: Dict[str, str]
        """
        raise NotImplementedError

    def set_state(self, session,  save_data):
        """ Recreates entity from saved data

        :param tuxemon.core.session.Session session:
        :param Dict save_data: Data used to recreate the Entity
        :rtype: Dict[str, str]
        """
        raise NotImplementedError
