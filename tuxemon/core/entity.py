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

from tuxemon.core.euclid import Point2, Vector3, Point3
from tuxemon.core.map import proj


class Entity:
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
        self.tile_pos = Point2(0, 0)
        self.position3 = Point3(0, 0, 0)
        self.acceleration3 = Vector3(0, 0, 0)  # not used currently, just set velocity
        self.velocity3 = Vector3(0, 0, 0)
        self.update_location = False

    # === PHYSICS START ================================================================
    def stop_moving(self):
        """ Completely stop all movement

        :return: None
        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def pos_update(self):
        """ WIP.  Required to be called after position changes

        :return:
        """
        self.tile_pos = proj(self.position3)

    def update_physics(self, td):
        """ Move the entity according to the movement vector

        :param td:
        :return:
        """
        self.position3 += self.velocity3 * td
        self.pos_update()

    def set_position(self, pos):
        """ Set the entity's position in the game world

        :param pos:
        :return:
        """
        self.position3.x = pos[0]
        self.position3.y = pos[1]
        self.pos_update()

    # === PHYSICS END ==================================================================

    @property
    def moving(self):
        """ Is the entity moving?

        :rtype: bool
        """
        return not self.velocity3 == (0, 0, 0)

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
