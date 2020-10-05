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

from tuxemon.core import prepare
from tuxemon.core.event.eventaction import EventAction


class TeleportAction(EventAction):
    """Teleport the player to a particular map and tile coordinates

    Valid Parameters: map_name, coordinate_x, coordinate_y

    **Examples:**

    >>> action.__dict__
    {
        "type": "teleport",
        "parameters": [
            "taba_town.tmx",
            "5",
            "5"
        ]
    }

    """
    name = "teleport"
    valid_parameters = [
        (str, "map_name"),
        (int, "x"),
        (int, "y")
    ]

    def start(self):
        player = self.session.player
        world = self.session.client.get_state_by_name("WorldState")
        map_name = self.parameters.map_name

        # If we're doing a screen transition with this teleport, set the map name that we'll
        # load during the apex of the transition.
        # TODO: This only needs to happen once.
        if world.in_transition:
            world.delayed_mapname = map_name

        # Check to see if we're also performing a transition. If we are, wait to perform the
        # teleport at the apex of the transition
        if world.in_transition:
            # the world state will handle the teleport/transition, hopefully
            world.delayed_teleport = True
            world.delayed_x = self.parameters.x
            world.delayed_y = self.parameters.y

        else:
            # If we're not doing a transition, then just do the teleport
            map_path = prepare.fetch("maps", map_name)

            if world.current_map is None:
                world.change_map(map_path)

            elif map_path != world.current_map.filename:
                world.change_map(map_path)

            # Stop the player's movement so they don't continue their move after they teleported.
            player.cancel_path()

            # must change position after the map is loaded
            player.set_position((self.parameters.x, self.parameters.y))

            # unlock_controls will reset controls, but start moving if keys are pressed
            world.unlock_controls()

