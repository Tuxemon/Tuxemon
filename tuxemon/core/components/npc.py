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
import os
import logging

import pygame

from core.tools import load_and_scale, nearest
from core.components import db, pyganim
from core.components.euclid import Point3, Vector3, Point2
from core.components.locale import translator
from core.components.map import facing, proj, dirs2, dirs3, get_direction

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


class Entity(object):
    """ Eventually a class for all things that exist on the
        game map, like NPCs, players, objects, etc
    """
    pass


class Npc(Entity):
    """ Class for humanoid type game objects, NPC, Players, etc
    """

    def __init__(self, npc_slug):

        # load initial data from the npc database
        npcs = db.JSONDatabase()
        npcs.load("npc")
        npc_data = npcs.lookup(npc_slug, table="npc")

        # This is the player's name to be used in dialog
        self.name = trans(npc_data["name_trans"])

        # Hold on the the string so it can be sent over the network
        self.sprite_name = npc_data["sprite_name"]

        # Whether or not this player has AI associated with it
        self.ai = None

        # used for various tests, idk
        self.isplayer = False

        # physics.  eventually move to a mixin/component.
        # these coordinates/values are derived from the tile position.
        self.position3 = Point3(0, 0, 0)
        self.velocity3 = Vector3(0, 0, 0)
        self.acceleration3 = Vector3(0, 0, 0)
        self.tile_pos = Point2(0, 0)

        self.walkrate = 3.75  # The rate in tiles per second the player is walking
        self.runrate = 7.35  # The rate in tiles per second the player is running
        self.moverate = self.walkrate  # The movement rate in pixels per second
        self.walking = False  # Whether or not the player is walking
        self.running = False  # Whether or not the player is running
        self.move_direction = "down"  # This is a string of the direction we're moving if we're in the middle of moving

        # used when following a path
        self.start_position = None

        # distance is used to prevent erratic framerates causing the npc
        # to overshoot the waypoint and continue on
        self.waypoint_distance = 0

        # Next point to reach when following a path
        self.waypoint_destination = Point2(0, 0)

        # end physics

        # for networking, maybe?
        self.update_location = False

        self.standing = {}
        self.facing = "down"  # What direction the player is facing

        self.world = None
        self.path = None
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client
        self.inventory = {}  # The Player's inventory.
        self.behavior = "wander"
        self.interactions = []  # List of ways player can interact with the Npc

        # TODO: move sprites out so class can be used headless
        self.playerHeight = 0
        self.playerWidth = 0
        self.moveConductor = None
        self.sprite = {}  # The pyganim object that contains the player animations
        self.load_sprites()
        self.rect = pygame.Rect(self.tile_pos, (self.playerWidth, self.playerHeight))  # Collision rect

        # required to initialize position and velocity
        self.stop_moving()

    def load_sprites(self):
        """ Load sprite graphics

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
        self.moveConductor = pyganim.PygConductor(self.sprite)

    # === PHYSICS START ================================================================

    def suppress_movement(self):
        """ Stop movement while keeping track of control state

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
        """ Move the entity with respect to the movement vector

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
        self.moveConductor.play()

    def stop_moving(self):
        """ Completely stop all movement; reset control state

        :return:
        """
        self.moveConductor.stop()
        self.set_position(nearest(self.position3))
        self.waypoint_destination = None
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    @property
    def moving(self):
        """ Is the entity moving?

        :rtype: bool
        """
        return not self.velocity3 == (0, 0, 0)

    # === PHYSICS END ==================================================================

    def move(self, time_passed_seconds, world):
        """ Move the entity around the game world

        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.
        :param world: The Tuxemon game instance itself.

        :type time_passed_seconds: Float
        :type world: core.states.world.worldstate.WorldState
        """
        # TODO: eventually move to an world/environment class
        self.world = world

        # does the npc want to move?
        if self.move_direction and not self.moving:
            self.move_one_tile(self.move_direction)

        if self.path and self.waypoint_destination is None:
            self.next_waypoint()

        if self.waypoint_destination is not None:
            self.continue_path()

        self.moverate = self.runrate if self.running else self.walkrate
        self.update_physics(time_passed_seconds)

        # if not self.moving:
        #     if self.isplayer and self.tile_pos != self.final_move_dest:
        #         self.update_location = True

    def move_one_tile(self, direction=None):
        """ Ask entity to move one tile in move direction

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

        if destination in self.world.get_exits(origin):
            self.set_path([destination])

    def set_path(self, path):
        """ Sets the path for the entity to follow.

        If there is no path now, it will be set and started
        If a path is being followed, this will cancel it and start new

        :return: None
        """
        self.path = path

    def _force_continue_move(self, collision_dict):
        pos = nearest(self.tile_pos)
        if pos in collision_dict:
            direction_next = collision_dict[pos]["continue"]
            self.move_one_tile(direction_next)

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

    def get_sprites(self):
        """ Get the surfaces and layers for the sprite

        Used to render the player

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
