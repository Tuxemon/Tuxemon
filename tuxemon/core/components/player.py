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
"""This module contains the player and npc modules.
"""
from __future__ import absolute_import, division

import logging
import os

import pygame

from core.components import db, pyganim
from core.components.euclid import Point2, Point3, Vector3
from core.components.locale import translator
from core.tools import load_and_scale, nearest

trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

# direction => vector
dirs = {
    "up": Vector3(0, -1, 0),
    "down": Vector3(0, 1, 0),
    "left": Vector3(-1, 0, 0),
    "right": Vector3(1, 0, 0),
}

# complimentary directions
pairs = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left"
}

facing = "front", "back", "left", "right"

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


def get_direction(start, end):
    if start[0] > end[0]:
        return "left"
    elif start[0] < end[0]:
        return "right"
    elif start[1] < end[1]:
        return "down"
    elif start[1] > end[1]:
        return "up"


def proj(point):
    """ Project 3d coordinates to 2d.
    Not necessarily for use on a screen.

    :param point:
    :return:
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


class Entity(object):
    pass


class Npc(Entity):
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
        self.isplayer = False

        # physics.  eventually move to a mixin/component
        # these positions are derived from the tile position.
        self.position3 = Point3(0, 0, 0)
        self.velocity3 = Vector3(0, 0, 0)
        self.acceleration3 = Vector3(0, 0, 0)
        self.tile_pos = Point2(0, 0)

        self.walkrate = 3.75  # The rate in tiles per second the player is walking
        self.runrate = 7.35  # The rate in tiles per second the player is running
        self.moverate = self.walkrate  # The movement rate in pixels per second
        self.walking = False  # Whether or not the player is walking
        self.running = False  # Whether or not the player is running

        self.start_position = None
        self.move_direction = "down"  # This is a string of the direction we're moving if we're in the middle of moving
        self.move_destination = Point2(0, 0)  # The player's destination location to move to
        # end physics

        # for networking, maybe?
        self.update_location = False

        self.standing = {}
        self.sprite = {}  # The pyganim object that contains the player animations
        self.direction = {}  # What direction the player wants to move
        self.facing = "down"  # What direction the player is facing

        self.game = None
        self.path = None
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client
        self.inventory = {}  # The Player's inventory.
        self.behavior = "wander"
        self.interactions = []  # List of ways player can interact with the Npc

        # TODO: move out so class can be used headless
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

    def move(self, time_passed_seconds, game):
        """ Move the entity around the game world

        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.
        :param game: The Tuxemon game instance itself.

        :type time_passed_seconds: Float
        :type game: core.states.world.worldstate.WorldState
        """
        self.game = game

        collision_dict = game.get_collision_dict(self)
        blocked = self.collision_check(collision_dict, game.collision_lines_map)

        # check player input and move if needed
        # moving works by making a one tile path
        direction = self._check_input(blocked)
        if direction:
            self.move_one_tile(direction)

        # if the self has a path, move it along its path
        if self.path and self.move_destination is None:
            self.start_path()

        if self.move_destination is not None:
            self.continue_path()

        self.moverate = self.runrate if self.running else self.walkrate
        self.update_physics(time_passed_seconds)

        # if self.moving:
        #     self._continue_move(blocked)
        #     self._force_continue_move(collision_dict)

        #
        #         # test again, since may have stopped above
        #         if self.moving:
        #             v = dirs[self.move_direction]
        #             self.velocity3 = self.moverate * v
        #     else:
        #         self._check_move(c)
        #
        #         # if not self.moving:
        #         #     if self.isplayer and self.tile_pos != self.final_move_dest:
        #         #         self.update_location = True
        #
        #         # # Reset our directions after moving.
        #         # if not self.isplayer:
        #         #     self.direction["up"] = False
        #         #     self.direction["down"] = False
        #         #     self.direction["left"] = False
        #         #     self.direction["right"] = False

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

    def stop_moving(self):
        """ Completely stop all movement; reset control state

        :return:
        """
        self.moveConductor.stop()
        self.set_position(nearest(self.position3))
        self.move_direction = None
        self.move_destination = None
        self.direction['up'] = False
        self.direction['down'] = False
        self.direction['left'] = False
        self.direction['right'] = False
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    # === PHYSICS END ==================================================================

    def move_one_tile(self, direction):
        """ Force entity to move one tile in a direction

        Internally just sets a path for an adjacent tile

        :type direction: str
        :param direction: up, down, left right

        :return: None
        """
        pos = Point2(*nearest(self.tile_pos))
        v = dirs[direction]
        self.set_path([pos + (v.x, v.y)])

    def set_path(self, path):
        """ Sets the path for the entity to follow.

        If there is no path now, it will be set and started
        If a path is being followed, this will cancel it and start new

        :return: None
        """
        print("set", path, self.tile_pos)
        self.path = path

    def _check_input(self, blocked_directions):
        """ Check if a player input is valid to move

        :param blocked_directions: list of directions that cannot be traveled

        :return:
        """
        for direction, pressed in self.direction.items():
            if pressed and direction not in blocked_directions:
                return direction

    def _continue_move(self, blocked_directions):
        """ Here we're continuing a move it we're in the middle of one already

        If the player is in the middle of moving and facing a certain direction, move in that
        direction
        """
        dest_dist = self.start_position.distance(self.move_destination)
        remaining = self.start_position.distance(self.tile_pos)
        reached = dest_dist <= remaining

        # prevent issues when changing facing while walking
        self.facing = self.move_direction

        if reached:
            self.set_position(self.move_destination)
            if self.direction[self.move_direction]:
                if self.move_direction in blocked_directions:
                    self.stop_moving()
                else:
                    self.move_one_tile(self.move_direction)
            else:
                for direction, held in self.direction.items():
                    if held and direction not in blocked_directions:
                        self.move_one_tile(direction)
                        break
                else:
                    self.stop_moving()

    def _force_continue_move(self, collision_dict):
        pos = nearest(self.tile_pos)
        if pos in collision_dict:
            direction_next = collision_dict[pos]["continue"]
            self.move_one_tile(direction_next)

    def start_path(self):
        """
        This method will ensure movement will happen until the player
        reaches its destination
        """
        # if not self.moving:
        #     if self.isplayer and (self.game.game.isclient or self.game.game.ishost):
        #         self.game.game.client.update_player("up", event_type="CLIENT_MOVE_START")
        start_position = Point2(*nearest(self.tile_pos))
        move_destination = Point2(*self.path.pop())

        # path may be for the tile currently on
        if start_position == move_destination:
            return

        self.move_direction = get_direction(start_position, move_destination)
        self.start_position = start_position
        self.move_destination = move_destination
        self.start_moving()

    def start_moving(self):
        self.facing = self.move_direction
        self.velocity3 = self.moverate * dirs[self.move_direction]
        self.pos_update()
        self.moveConductor.play()

    def continue_path(self):
        # euclid.py will choke and die if you check the distance between
        # points with the same coordinates, so this distance test needs to
        # be handled carefully by checking if they are the same first
        if not self.start_position == self.tile_pos:
            dest_dist = self.start_position.distance(self.move_destination)
            remaining = self.start_position.distance(self.tile_pos)
            reached = dest_dist <= remaining

            if reached:
                print("reached", self.path)
                self.set_position(self.move_destination)
                self.move_destination = None
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

        direction = self.move_direction if self.moving else self.facing
        frame_dict = self.sprite if self.moving else self.standing
        state = animation_mapping[self.moving][direction]

        return [(get_frame(frame_dict, state), self.tile_pos, 2)]

    def collision_check(self, collision_dict, collision_lines_map):
        """ Checks collision tiles and NPCs' around the player.

        Slow operation.  Be sure to cache results.

        TODO: move to the map layer

        :param collision_dict: A dictionary object of (x, y) coordinates that are collidable.
        :type collision_dict: dict
        :rtype: list
        :returns: A list indicating what tiles relative to the player are collision tiles.
            e.g. ["down", "up"]

        """
        # TODO: eventually move to Map Class (core/components/map.py)
        collisions = []
        position = nearest(self.tile_pos)

        # Check if the players current position has any limitations.
        tile = collision_dict.get(position)

        if tile is not None:

            try:
                exits = tile["exit"]
            except:
                print(self, "collide", tile, position)
                # collisions.append(direction)

            else:
                for direction in dirs:
                    if direction not in exits:
                        collisions.append(direction)

        for direction, offset in dirs.items():
            tile = proj(nearest(self.position3 + offset))
            blocker = collision_dict.get(tile)
            if blocker is not None:
                collisions.append(direction)

        # From the players current tile, check to see if any nearby tile
        # is separated by a wall
        # for tile, direction in collision_lines_map:
        #     if position == tile:
        #         collisions.append(direction)

        # Return a list of all the collision tiles around the player.
        return collisions

    def pathfind(self, dest, world_map):
        """ Pathfind

        :type dest: tuple
        :type world_map: core.components.map.Map

        :return:
        """
        return
        # first check npc doesn't already have a path
        if not self.path:
            # will generate a path and store it in
            # player.path
            starting_loc = nearest(self.tile_pos)

            pathnode = self.pathfind_r(dest,
                                       [PathfindNode(starting_loc)],  # queue
                                       [],  # visited
                                       0,  # depth (not a limit, just a counter)
                                       world_map)
            if pathnode:
                # traverse the node to get the path
                path = []
                while pathnode:
                    path.append(pathnode.get_value())
                    pathnode = pathnode.get_parent()

                # last minute check to remove the top _plan step if
                # it's the same as our location
                if path[len(path) - 1] == self.tile_pos:
                    path.pop()

                # store the path
                self.set_path(path)

            else:
                # TODO get current map name for a more useful error
                logger.error("Pathfinding failed to find a path from " +
                             str(starting_loc) + " to " + str(dest) +
                             ". Are you sure that an obstacle-free path exists?")

    def pathfind_r(self, dest, queue, visited, depth, world_map):
        """ Recursive breadth first search algorithm

        :type dest: tuple
        :type queue: list
        :type visited: list
        :type depth: int
        :type world_map: core.states.world.worldstate.WorldState
        
        :rtype: list
        """
        if not queue:
            # does reaching this case mean we exhausted the search?
            # I think so which means there is no possible path
            return False

        elif queue[0].get_value() == dest:
            # done
            return queue[0]

        else:
            # sort the queue by node depth
            queue = sorted(queue, key=lambda x: x.get_depth())

            # pop next tile off queue
            next_node = queue.pop(0)

            # add neighbors of current tile to queue
            # if we haven't checked them already
            for adj_pos in self.get_adjacent_tiles(next_node.get_value(), world_map):
                if adj_pos not in visited and adj_pos not in map(lambda x: x.get_value(), queue):
                    queue = [PathfindNode(adj_pos, next_node)] + queue
                    visited = [next_node.get_value()] + visited

            # recur
            path = self.pathfind_r(dest, queue, visited, depth + 1, world_map)
            return path

    def get_adjacent_tiles(self, position, world):
        """ Return list of tiles which can be moved into

        :param position:
        :type world: core.states.world.worldstate.WorldState
        :rtype: list
        """
        collision_map = world.get_collision_dict(self)
        blocked_directions = self.collision_check(collision_map, world.collision_lines_map)
        adj_tiles = []
        if "up" not in blocked_directions:
            adj_tiles.append((position[0], position[1] - 1))
        if "down" not in blocked_directions:
            adj_tiles.append((position[0], position[1] + 1))
        if "left" not in blocked_directions:
            adj_tiles.append((position[0] - 1, position[1]))
        if "right" not in blocked_directions:
            adj_tiles.append((position[0] + 1, position[1]))
        return adj_tiles

    @property
    def moving(self):
        """ Is the entity moving?

        :rtype: bool
        """
        return not self.velocity3 == (0, 0, 0)


# Class definition for the player.
class Player(Npc):
    """ This object can be used for NPCs as well as the player
    """
    # The maximum number of tuxemon this player can hold
    party_limit = 6
    isplayer = True

    def __init__(self, npc_slug):
        super(Player, self).__init__(npc_slug)

        # Game variables for use with events
        self.game_variables = {}

        # This is a list of tuxemon the player has
        self.monsters = []
        self.storage = {"monsters": [], "items": {}}

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
        # Remove the tuxemon if they are in this player's party
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


class PathfindNode(object):
    """ Used in path finding search
    """

    def __init__(self, value, parent=None):
        self.parent = parent
        self.value = value
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent
        self.depth = parent.depth + 1

    def get_value(self):
        return self.value

    def get_depth(self):
        return self.depth

    def __str__(self):
        s = str(self.value)
        if self.parent is not None:
            s += str(self.parent)
        return s
