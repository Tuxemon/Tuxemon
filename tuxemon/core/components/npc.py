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
# core.components.npc
#
from math import hypot
import logging
import os

import pygame

from core.components import db, pyganim
from core.components.entity import Entity
from core.components.locale import translator
from core.components.map import facing, dirs3, dirs2, get_direction
from core.tools import load_and_scale, trunc, nearest

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
    # The maximum number of tuxemon this npc can hold
    party_limit = 6

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
        self.interactions = []  # List of ways player can interact with the Npc

        # used for various tests, idk
        self.isplayer = False

        # pathfinding and waypoint related
        self.path = []
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client

        self.move_direction = None  # Set this value to move the npc (see below)
        self.facing = "down"  # Set this value to change the facing direction
        self.walking = False  # Whether or not the player is walking
        self.running = False  # Whether or not the player is running
        self.walkrate = 3.75  # The rate in tiles per second the player is walking
        self.runrate = 7.35  # The rate in tiles per second the player is running
        self.moverate = self.walkrate  # walk by default

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction.
        # This will not change facing, that must be changed as well.
        # The facing and movement values are separate to allow advanced movement, like strafing.

        # TODO: move sprites into renderer so class can be used headless
        self.playerHeight = 0
        self.playerWidth = 0
        self.standing = {}  # Standing animation frames
        self.sprite = {}  # Moving animation frames
        self.moveConductor = pyganim.PygConductor()
        self.load_sprites()
        self.rect = pygame.Rect(self.tile_pos, (self.playerWidth, self.playerHeight))  # Collision rect

        self.monsters = []  # This is a list of tuxemon the npc has
        self.inventory = {}  # The Player's inventory.
        self.storage = {"monsters": [], "items": {}}

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

    def pathfind(self, destination):
        self.path = self.world.pathfind(tuple(self.tile_pos), destination)

    def _force_continue_move(self, collision_dict):
        pos = nearest(self.tile_pos)
        if pos in collision_dict:
            direction_next = collision_dict[pos]["continue"]
            self.move_one_tile(direction_next)

    def stop_moving(self):
        """ Completely stop all movement

        :return: None
        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def move(self, time_passed_seconds):
        """ Move the entity around the game world

        * check if the move_direction variable is set
        * set the movement speed
        * follow waypoints
        * control walking animations
        * send network updates

        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.

        :type time_passed_seconds: Float
        """
        self.moverate = self.runrate if self.running else self.walkrate

        # update physics.  eventually move to another class
        self.update_physics(time_passed_seconds)

        if self.path:
            self.check_waypoint()

        # does the npc want to move?
        if self.move_direction:
            if not self.path:
                self.move_one_tile(self.move_direction)
                self.moveConductor.play()
                self.next_waypoint()

        # TODO: determine way to tell if another force is moving the entity
        # TODO: basically, this simple check will only allow player movement
        # TODO: its not possible to move the entity with physics b/c this stops that
        if not self.path:
            self.stop_moving()
            self.moveConductor.stop()

            # TODO: enable and test this network code
            # if not self.moving:
            #     if self.isplayer and (self.game.game.isclient or self.game.game.ishost):
            #         self.game.game.client.update_player("up", event_type="CLIENT_MOVE_START")

            # if not self.moving:
            #     if self.isplayer and self.tile_pos != self.final_move_dest:
            #         self.update_location = True

    def move_one_tile(self, direction):
        """ Ask entity to move one tile

        Internally just sets a path for an adjacent tile.

        :type direction: str
        :param direction: up, down, left right

        :return: None
        """
        self.path.append(trunc(self.tile_pos + dirs2[direction]))

    def valid_movement(self, tile):
        return tile in self.world.get_exits(trunc(self.tile_pos))

    def check_waypoint(self):
        """ Check if the waypoint is reached

        :return:
        """
        target = self.path[-1]
        x0, y0 = self.tile_pos
        x1, y1 = target
        distance = hypot(x1 - x0, y1 - y0)
        if distance < .05:
            self.set_position(target)
            self.path.pop()
            if self.path:
                self.next_waypoint()

    def next_waypoint(self):
        """ Take the next step of the path, stop if way is blocked
        """
        target = self.path[-1]
        if self.valid_movement(target):
            direction = get_direction(self.tile_pos, target)
            self.facing = direction
            self.velocity3 = self.moverate * dirs3[direction]
        else:
            self.path.pop()

    ####################################################
    #                   Monsters                       #
    ####################################################
    def add_monster(self, monster):
        """Adds a monster to the player's list of monsters. If the player's party is full, it
        will send the monster to PCState archive.

        :param monster: The core.components.monster.Monster object to add to the player's party.

        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None

        """
        if len(self.monsters) >= self.party_limit:
            self.storage["monsters"].append(monster)
        else:
            self.monsters.append(monster)

    def find_monster(self, monster_slug):
        """Finds a monster in the player's list of monsters.

        :param monster_slug: The slug name of the monster
        :type monster_slug: str

        :rtype: core.components.monster.Monster
        :returns: Monster found
        """
        for monster in self.monsters:
            if monster.slug == monster_slug:
                return monster
        return None

    def remove_monster(self, monster):
        """ Removes a monster from this player's party.

        :param monster: Monster to remove from the player's party.

        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None
        """
        if monster in self.monsters:
            self.monsters.remove(monster)

    def switch_monsters(self, index_1, index_2):
        """ Swap two monsters in this player's party

        :param index_1/index_2: The indexes of the monsters to switch in the player's party.

        :type index_1: int
        :type index_2: int

        :rtype: None
        :returns: None
        """
        self.monsters[index_1], self.monsters[index_2] = self.monsters[index_2], self.monsters[index_1]
