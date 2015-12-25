#!/usr/bin/python
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
# William Edwards <shadowapex@gmail.com>
# Derek Clark <derekjohn.clark@gmail.com>
#
# core.components.middleware
#
"""This module contains the Tuxemon server middleware.
"""
import logging

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

class Multiplayer():
    """This middleware will allow you to use the AsteriaServer for Multiplayer games and the mobile controller. 
    When it receives KEYDOWN/KEYUP/NETKBD events, it will set the corresponding dictionary key in 
    "network_events" to true or false. In your main game loop, you can then iterate through this dictionary 
    and change the game accordingly.

    Public functions:
    event_legal -- Returns True for all events that pass the legal logic. Returns False for all events that 
                   fail legal logic.
    event_execute -- Sets the game_server.network_events dictionary based on what key was pressed

    """
    def __init__(self, game_server=None):
        self.game_server = game_server
        self.server = None

    def event_legal(self, cuuid, euuid, event_data):
        if event_data["type"] == "PUSH_SELF":
            return True
        if event_data["type"] == "CLIENT_MOVE_START": 
            return True
        if event_data["type"] == "CLIENT_MAP_UPDATE":
            return True
        if event_data["type"] == "CLIENT_MOVE_COMPLETE":
            return True
        if event_data["type"] == "CLIENT_KEYDOWN":
            return True
        if event_data["type"] == "CLIENT_KEYUP":
            return True
        if event_data["type"] == "CLIENT_FACING":
            return True
        if event_data["type"] == "CLIENT_INTERACTION":
            return True
        if event_data["type"] == "CLIENT_RESPONSE":
            return True
        if event_data["type"] == "CLIENT_START_BATTLE":
            return True
        if event_data["type"] == "PING":
                return True
        else:
            return False

    def event_execute(self, cuuid, euuid, event_data):
        self.game_server.server_event_handler(cuuid, event_data)

class Controller():
    """This middleware will allow you to use the AsteriaServer for Multiplayer games and the mobile controller. 
    When it receives KEYDOWN/KEYUP events, it will set the corresponding dictionary key in 
    "network_events" to true or false. In your main game loop, you can then iterate through this dictionary 
    and change the game accordingly.

    Public functions:
    event_legal -- Returns True for all events that pass the legal logic. Returns False for all events that 
                   fail legal logic.
    event_execute -- Sets the game_server.network_events dictionary based on what key was pressed

    """
    def __init__(self, game_server=None):
        self.game_server = game_server
        self.server = None

    def event_legal(self, cuuid, euuid, event_data):
        if "KEYDOWN:" in event_data or "KEYUP:" in event_data:
            return True
    
    def event_execute(self, cuuid, euuid, event_data):
        if "KEYDOWN:" in event_data or "KEYUP:" in event_data:
            self.game_server.network_events.append(event_data)
            