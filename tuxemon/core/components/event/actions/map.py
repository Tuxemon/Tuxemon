#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
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
#
from __future__ import absolute_import

import logging
import os
import re

import pygame

from core import prepare
from core.components import pyganim

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Map(object):

    def preload_map(self, game, action):
        """Preloads a map into memory for quick map switching

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: map_name

        **Examples:**

        >>> action.__dict__
        {
            "type": "preload_map",
            "parameters": [
                "map1.tmx"
            ]
        }

        """
        if not hasattr(game.current_state, 'state') or game.current_state.state != "WorldState":
            return
        world = game.current_state

        # Get the map name to preload
        mapname = prepare.BASEDIR + "resources/maps/" + str(action.parameters[0])

        if mapname not in world.preloaded_maps.keys():
            # TODO: We should do this asyncronously?
            print ("PRELOADING MAP:", mapname)
            world.preload_map(mapname)


    def screen_transition(self, game, action):
        """Initiates a screen transition

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: transition_time_in_seconds

        **Examples:**

        >>> action.__dict__
        {
            "type": "screen_transition",
            "parameters": [
                "1"
            ]
        }

        """

        world = game.get_state_name("WorldState")
        if not world.in_transition:
            world.fade_and_teleport(float(action.parameters[0]))


    def start_cinema_mode(self, game, action):
        """Starts cinema mode by animating moving black bars to narrow the aspect ratio.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None
        """

        world = game.current_state
        if world.cinema_state == "off":
            world.cinema_state = "turning on"


    def stop_cinema_mode(self, game, action):
        """Stops cinema mode by animating moving black bars to back to the normal aspect ratio.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None
        """

        world = game.current_state
        if world.cinema_state == "on":
            logger.info("Turning off cinema mode")
            world.cinema_state = "turning off"


    def play_map_animation(self, game, action):
        """Plays a map animation at a given position in the world map.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: animation_name,duration,loop,pos_x,pos_y

        * animation_name - The name of the animation stored under resources/animations/tileset.
            For example, an animation called "grass" will load frames called "grass.xxx.png".
        * duration - The duration of each frame of the animation in seconds.
        * loop - Can be either "loop" or "noloop" to loop the animation.
        * position - Can be either an x,y coordinate or "player" to draw the animation at the
            player's location.

        """

        # ('play_animation', 'grass,1.5,noloop,player', '1', 6)
        # "position" can be either a (x, y) tile coordinate or "player"
        animation_name = action.parameters[0]
        duration = float(action.parameters[1])
        directory = prepare.BASEDIR + "resources/animations/tileset"

        if action.parameters[2] == "loop":
            loop = True
        elif action.parameters[2] == "noloop":
            loop = False

        # Determine the screen position where to draw the animation.
        if action.parameters[3] == "player":
            position = (game.player1.tile_pos[0],
                        game.player1.tile_pos[1])

        else:
            position = (int(action.parameters[3]), int(action.parameters[4]))

        # Check to see if this animation has already been loaded.
        # If it has, play the animation using the animation's conductor.
        if animation_name in game.animations:
            game.animations[animation_name]["position"] = position
            game.animations[animation_name]["conductor"].play()
            return True

        # Loop through our animation resources and find the animation files based on name.
        scale = prepare.SCALE
        images_and_durations = []
        for animation_frame in os.listdir(directory):
            pattern = animation_name + "\.[0-9].*"
            if re.findall(pattern, animation_frame):
                frame = pygame.image.load(directory + "/" + animation_frame).convert_alpha()
                frame = pygame.transform.scale(frame, (frame.get_width() * scale, frame.get_height() * scale))
                images_and_durations.append((frame, duration))

        # Scale the animations based on our game's scale: world.scale

        # Create an animation object and conductor.
        animation = pyganim.PygAnimation(images_and_durations, loop=loop)
        conductor = pyganim.PygConductor({'animation': animation})
        conductor.play()

        game.animations[animation_name] = {"animation": animation,
                                           "conductor": conductor,
                                           "position": position,
                                           "layer": 3}
