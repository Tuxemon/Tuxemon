# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

import logging

from core import prepare
from core.components.event.eventaction import EventAction

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class PreloadMapAction(EventAction):
    """Preloads a map into memory for quick map switching

    Valid Parameters: map_name

    **Examples:**
    """
    name = "preload_map"
    valid_parameters = [
        (str, "map_name"),
    ]

    def start(self):
        if not hasattr(self.game.current_state, 'state') or self.game.current_state.state != "WorldState":
            return

        world = self.game.current_state

        # Get the map name to preload
        mapname = prepare.BASEDIR + prepare.DATADIR + "/maps/" + str(self.parameters[0])

        if mapname not in world.preloaded_maps.keys():
            # TODO: We should do this asyncronously?
            logger.debug("preloading map: {}".format(mapname))
            world.preload_map(mapname)
