#!/usr/bin/python
#
# Asteria
# Copyright (C) 2013, William Edwards <shadowapex@gmail.com>
#
# This file is part of Asteria.
#
# Asteria is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Asteria is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Asteria.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# middleware.py Legal processing of event data
#
#

import logging

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

class Anarchy():
    """This is the most basic middleware you can have. With it, all events sent to it will return legal
    no matter what. To make the middleware perform in-game events in response to network events, extend
    the "event_execute" method with what actions you wish to perform.

    Public functions:
    event_legal -- Returns true for all events
    event_execute -- Does nothing. Can be extended to modify variables/run in-game functions.

    """
    def __init__(self, game_server=None):
        self.game_server = game_server
        self.server = None

    def event_legal(self, cuuid, euuid, event_data):
        return True

    def event_execute(self, cuuid, euuid, event_data):
        pass


class Controller():
    """This middleware will allow you to use the AsteriaServer as a basic controller. When it receives 
    KEYDOWN/KEYUP events, it will set the corresponding dictionary key in "network_events" to true or
    false. In your main game loop, you can then iterate through this dictionary and change the game
    accordingly.

    Public functions:
    event_legal -- Returns true for all events
    event_execute -- Sets the game_server.network_events dictionary based on what key was pressed

    """
    def __init__(self, game_server=None):
        self.game_server = game_server
        self.server = None

    def event_legal(self, cuuid, euuid, event_data):
        if "KEYDOWN:" in event_data or "KEYUP:" in event_data:
            return True
        else:
            return False

    def event_execute(self, cuuid, euuid, event_data):
        self.game_server.network_events.append(event_data)
