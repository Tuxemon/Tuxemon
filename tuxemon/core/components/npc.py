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
# Leif Theden <leif.theden@gmail.com>
#
# core.components.player
#
import logging
import os

import pygame

from core.components import db, pyganim
from core.components.entity import Entity
from core.components.euclid import Point2
from core.components.locale import translator
from core.components.map import facing, dirs3, dirs2, get_direction
from core.tools import load_and_scale, nearest

trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

# reference direction and movement states to animation names
# this dictionary is kinda wip, idk
animation_mapping = {
    True: {
        'up': 'back_walk',
        'down': 'front_walk',
        'left': 'left_walk',
        'right': 'right_walk'},
    False: {
        'up': 'back',
        'down': 'front',
        'left': 'left',
        'right': 'right'}
}


class Npc(Entity):
    """ Class for humanoid type game objects, NPC, Players, etc
    """

    def __init__(self, npc_slug):
        super(Npc, self).__init__()

        # load initial data from the npc database
        npcs = db.JSONDatabase()
        npcs.load("npc")
        npc_data = npcs.lookup(npc_slug, table="npc")

        self.slug = npc_slug

        # This is the player's name to be used in dialog
        self.name = trans(npc_data["name_trans"])

        # Hold on the the string so it can be sent over the network
        self.sprite_name = npc_data["sprite_name"]

        # Whether or not this player has AI associated with it
        self.ai = None
        self.behavior = "wander"

        # used for various tests, idk
        self.isplayer = False

        self.facing = "down"  # Set this value to change the facing direction
        self.move_direction = None  # Set this value to move the npc (see below)
        self.walking = False  # Whether or not the player is walking
        self.running = False  # Whether or not the player is running
        self.walkrate = 3.75  # The rate in tiles per second the player is walking
        self.runrate = 7.35  # The rate in tiles per second the player is running
        self.moverate = self.walkrate  # walk by default

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction, then set the value to None.
        # This will not change facing, that must be changed as well.
        # The facing and movement values are separate to allow advanced movement, like strafing.

        self.path = []
        self.start_position = None
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client
        self.waypoint_distance = 0
        self.waypoint_destination = Point2(0, 0)

        self.inventory = {}  # The Player's inventory.
        self.interactions = []  # List of ways player can interact with the Npc

        # TODO: move sprites into renderer so class can be used headless
        self.playerHeight = 0
        self.playerWidth = 0
        self.standing = {}  # Standing animation frames
        self.sprite = {}  # Moving animation frames
        self.moveConductor = pyganim.PygConductor()
        self.load_sprites()
        self.rect = pygame.Rect(self.tile_pos, (self.playerWidth, self.playerHeight))  # Collision rect

        # required to initialize position and velocity
        self.stop_moving()

    def load_sprites(self):
        """ Load sprite graphics

        # TODO: refactor animations into renderer

        :return:
        """
        # Get all of the player's standing animation images.
        self.standing = {}
        for standing_type in facing:
            filename = "{}_{}.png".format(self.sprite_name, standing_type)
            path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)

        self.playerWidth, self.playerHeight = self.standing["front"].get_size()  # The player's sprite size in pixels

        # avoid cutoff frames when steps don't line up with tile movement
        frames = 3
        frame_duration = (1000 / self.walkrate) / frames / 1000 * 2

        # Load all of the player's sprite animations
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images_and_durations = [('sprites/%s_%s.%s.png' % (self.sprite_name, anim_type, str(num).rjust(3, '0')),
                                     frame_duration) for num in range(4)]

            # Loop through all of our animations and get the top and bottom subsurfaces.
            frames = []
            for image, duration in images_and_durations:
                surface = load_and_scale(image)
                frames.append((surface, duration))

            # Create an animation set for the top and bottom halfs of our sprite, so we can draw
            # them on different layers.
            self.sprite[anim_type] = pyganim.PygAnimation(frames, loop=True)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animtion
        # objects at the same time, so that way they'll always be in sync with each
        # other.
        self.moveConductor.add(self.sprite)

    def pathfind(self, destination):
        # pathfinding needs a tuple
        start = tuple(self.tile_pos)
        path = self.world.pathfind(start, destination)
        self.set_path(path)

    def _force_continue_move(self, collision_dict):
        pos = nearest(self.tile_pos)
        if pos in collision_dict:
            direction_next = collision_dict[pos]["continue"]
            self.move_one_tile(direction_next)

    def get_sprites(self):
        """ Get the surfaces and layers for the sprite

        Used to render the player

        # TODO: move out to the world renderer

        :return:
        """

        def get_frame(d, ani):
            frame = d[ani]
            try:
                surface = frame.getCurrentFrame()
                frame.rate = self.moverate / self.walkrate
                return surface
            except AttributeError:
                return frame

        frame_dict = self.sprite if self.moving else self.standing
        state = animation_mapping[self.moving][self.facing]

        return [(get_frame(frame_dict, state), self.tile_pos, 2)]

    def start_moving(self):
        """ Start moving

        :return:
        """
        # if not self.moving:
        #     if self.isplayer and (self.game.game.isclient or self.game.game.ishost):
        #         self.game.game.client.update_player("up", event_type="CLIENT_MOVE_START")
        self.facing = self.move_direction
        self.velocity3 = self.moverate * dirs3[self.move_direction]
        self.pos_update()

        if self.moveConductor.isStopped:
            self.moveConductor.play()

    def stop_moving(self):
        """ Completely stop all movement, snap to a tile location; reset control state

        :return: None
        """
        # snap position to nearest tile.
        # framerate jitters or other bugs may lead to incorrect positions.
        # this makes sure a NPC will always be centered on a tile.
        self.set_position(nearest(self.position3))

        # stop velocity
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

        # make sure wayfinding doesn't continue
        self.waypoint_destination = None

        # only stop animating if there is no path to follow
        if not self.move_direction:
            self.moveConductor.stop()

    def move(self, time_passed_seconds):
        """ Move the entity around the game world

        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.
        :param world: The Tuxemon game instance itself.

        :type time_passed_seconds: Float
        :type world: core.states.world.worldstate.WorldState
        """
        # does the npc want to move?
        if self.move_direction and not self.moving:
            self.move_one_tile(self.move_direction)

        # move towards next point on path, if needed
        if self.path and self.waypoint_destination is None:
            self.next_waypoint()

        # continue checking waypoint, if needed
        if self.waypoint_destination is not None:
            self.continue_path()

        self.moverate = self.runrate if self.running else self.walkrate

        # update physics.  eventually move to another class
        self.update_physics(time_passed_seconds)

        # if not self.moving:
        #     if self.isplayer and self.tile_pos != self.final_move_dest:
        #         self.update_location = True

    def move_one_tile(self, direction=None):
        """ Ask entity to move one tile

        If no direction is passed, use the facing direction.
        Will not move if the tile is blocked.
        Internally just sets a path for an adjacent tile.

        :type direction: str
        :param direction: up, down, left right

        :return: None
        """
        if direction is None:
            direction = self.facing

        origin = nearest(self.tile_pos)
        destination = nearest(self.tile_pos + dirs2[direction])

        # check if it is possible to move to destination
        if destination in self.world.get_exits(origin):
            self.path.append(destination)

    def set_path(self, path):
        """ Sets the path for the entity to follow.

        If there is no path now, it will be set and started
        If a path is being followed, this will cancel it and start new

        :return: None
        """
        self.path = path

    def next_waypoint(self):
        """ Take the next step of the path and set the next waypoint
        """
        start_position = Point2(*nearest(self.tile_pos))
        move_destination = Point2(*self.path.pop())

        # path may be for the tile currently on
        # if so, just give up!
        if start_position == move_destination:
            return

        self.move_direction = get_direction(start_position, move_destination)
        self.start_position = start_position
        self.waypoint_destination = move_destination
        self.waypoint_distance = self.start_position.distance(self.waypoint_destination)
        self.start_moving()

    def continue_path(self):
        """ Move towards next waypoint, stop if reached it

        :return:
        """
        # euclid.py will choke and die if you check the distance between points
        # with the same coordinates, so this distance test needs to be handled
        # carefully by checking if they are the same before checking distance
        if not self.start_position == self.tile_pos:
            remaining = self.start_position.distance(self.tile_pos)
            reached = self.waypoint_distance <= remaining

            if reached:
                self.set_position(self.waypoint_destination)
                self.waypoint_destination = None
                if not self.path:
                    self.stop_moving()
