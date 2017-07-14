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

from core import prepare
from core.components import db, pyganim
from core.components.euclid import Point2, Point3, Vector3
from core.components.locale import translator
from core.tools import load_and_scale, nearest

trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

dirs = {
    "up": Vector3(0, -1, 0),
    "down": Vector3(0, 1, 0),
    "left": Vector3(-1, 0, 0),
    "right": Vector3(1, 0, 0),
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


def proj(vector):
    return Point2(vector.x, vector.y)


# Class definition for the player.
class Player(object):
    """ This object can be used for NPCs as well as the player
    """

    def __init__(self, npc_slug):
        npcs = db.JSONDatabase()
        npcs.load("npc")
        npc_data = npcs.lookup(npc_slug, table="npc")

        self.name = trans(npc_data["name_trans"])  # This is the player's name to be used in dialog
        self.sprite_name = npc_data["sprite_name"]  # Hold on the the string so it can be sent over the network

        self.ai = None  # Whether or not this player has AI associated with it
        self.sprite = {}  # The pyganim object that contains the player animations

        # TODO: move out so class can be used headless
        self.standing = {}
        self.load_sprites()

        self.game_variables = {}  # Game variables for use with events
        self.inventory = {}  # The Player's inventory.
        self.monsters = []  # This is a list of tuxemon the player has
        self.storage = {"monsters": [], "items": {}}
        self.party_limit = 6  # The maximum number of tuxemon this player can hold 1 for testing

        self.game = None
        self.isplayer = True
        self.path = None
        self.walking = False  # Whether or not the player is walking
        self.running = False  # Whether or not the player is running
        self.move_direction = "down"  # This is a string of the direction we're moving if we're in the middle of moving
        self.direction = {"up": False,
                          "down": False,
                          "left": False,
                          "right": False}  # What direction the player wants to move
        self.facing = "down"  # What direction the player is facing
        self.tile_size = prepare.TILE_SIZE
        self.move_destination = Point2(0, 0)  # The player's destination location to move to
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client

        self.tile_pos = [0, 0]  # This is the position of the player based on tile position
        self.walkrate = 3.75 * 10  # The rate in tiles per second the player is walking
        self.runrate = 7.375 * 10  # The rate in tiles per second the player is running

        # physics.  eventually move to a mixin/component
        # these positions are derived from the tile position.
        # setting these will not change the world position of the npc
        self.position2 = Point2(0, 0)
        self.position3 = Point3(0, 0, 0)
        self.acceleration3 = Vector3(0, 0, 0)
        self.velocity3 = Vector3(0, 0, 0)
        # end physics

        self.rect = pygame.Rect(self.position2, (self.playerWidth, self.playerHeight))  # Collision rect
        self.walkrate *= prepare.SCALE
        self.runrate *= prepare.SCALE
        self.moverate = self.walkrate  # The movement rate in pixels per second

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

        # Load all of the player's sprite animations
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images_and_durations = [('sprites/%s_%s.%s.png' % (self.sprite_name, anim_type, str(num).rjust(3, '0')),
                                     prepare.CONFIG.player_animation_speed) for num in range(4)]

            # Loop through all of our animations and get the top and bottom subsurfaces.
            frames = []
            for image, duration in images_and_durations:
                surface = load_and_scale(image)
                frames.append((surface, duration))

            # Create an animation set for the top and bottom halfs of our sprite, so we can draw
            # them on different layers.
            self.sprite[anim_type] = pyganim.PygAnimation(frames)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animtion
        # objects at the same time, so that way they'll always be in sync with each
        # other.
        self.moveConductor = pyganim.PygConductor(self.sprite)
        self.moveConductor.play()

    def meta_move(self, tile_size, time_passed_seconds, game):
        if self.running:
            self.moverate = self.runrate
        else:
            self.moverate = self.walkrate

        # if the self has a path, move it along its path
        if self.path:
            self.move_by_path()

        self.move(tile_size, time_passed_seconds, game)

    def move(self, tile_size, time_passed_seconds, game):
        """ Draws text to the current menu object

        :param tile_size: A list with the [width, height] of the tiles in pixels. This is used for
            tile-based movement.
        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.
        :param game: The Tuxemon game instance itself.

        :type tile_size: List
        :type time_passed_seconds: Float
        :type game: core.control.Control
        """
        collision_dict = self.get_collision_dict(game)

        self.game = game

        # If the destination tile won't collide with anything, then proceed with moving.
        pos = nearest(self.tile_pos)
        c = self.collision_check(pos, collision_dict, game.collision_lines_map)

        if self.moving:
            self._continue_move(c)
            self._force_continue_move(collision_dict)
        else:
            self._check_move(c)

        self.update_physics(time_passed_seconds)
        self.tile_pos = Point2(self.position2.x / self.tile_size[0],
                               self.position2.y / self.tile_size[1])

    # === PHYSICS START ================================================================

    def update_physics(self, td):
        # no accel yet
        self.position3 += self.velocity3 * td
        self.position2 = proj(self.position3)

    @property
    def moving(self):
        return not self.velocity3 == (0, 0, 0)

    def stop(self):
        self.direction['up'] = False
        self.direction['down'] = False
        self.direction['left'] = False
        self.direction['right'] = False
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def set_position(self, pos):
        self.position3.x = pos[0]
        self.position3.y = pos[1]

    def set_tile_position(self, pos):
        x = pos[0] * self.tile_size[0]
        y = pos[1] * self.tile_size[1]
        self.set_position((x, y))

    # === PHYSICS END ==================================================================

    def _check_move(self, blocked_directions):
        """ Play the animation and setting a new destination if we currently don't have one

        player.direction is set when a key is pressed.
        player.moving is set when we're still in the middle of a move

        :param blocked_directions: list of directions that cannot be traveled
        :param game:
        :return:
        """
        for direction, pressed in self.direction.items():
            if pressed and direction not in blocked_directions:
                self.move_one_tile(direction)

                # break to ensure only one direction is processed
                break

                # # If we're not holding down an arrow key and the player is not moving, stop the animation
                # # and draw the standing gfx
                # if not self.moving:
                #     self.moveConductor.stop()
                #     if self.isplayer and self.tile_pos != self.final_move_dest:
                #         self.update_location = True

    def _continue_move(self, blocked_directions):
        """ Here we're continuing a move it we're in the middle of one already

        If the player is in the middle of moving and facing a certain direction, move in that
        direction
        """
        dest_dist = self.start_tile_position.distance(self.move_destination)
        remaining = self.start_tile_position.distance(self.tile_pos)
        reached = dest_dist <= remaining

        if reached:
            self.set_tile_position(self.move_destination)
            for direction, held in self.direction.items():
                if held and direction not in blocked_directions:
                    self.move_one_tile(direction)
                    break
            else:
                self.stop()

    def _force_continue_move(self, collision_dict):
        pos = nearest(self.tile_pos)

        if pos in collision_dict:
            direction_next = collision_dict[pos]["continue"]
            self.move_one_tile(direction_next)

    def move_one_tile(self, direction):
        """ Force player to move one tile in

        :param direction:
        :return:
        """
        if not self.moving:
            if self.isplayer and (self.game.game.isclient or self.game.game.ishost):
                self.game.game.client.update_player("up", event_type="CLIENT_MOVE_START")

        pos = Point2(*nearest(self.tile_pos))
        v = dirs[direction]
        self.start_tile_position = pos
        self.moveConductor.play()
        self.velocity3 = v * self.moverate
        self.move_destination = pos + (v.x, v.y)
        self.move_direction = direction

    def move_to(self, tile_pos, speed):
        """ Trigger NPC movement to the destination `tile_pos`

        * Only cardinal directions are guaranteed to work: left, right, up, down; no diagonals
        * Probably won't work on Player

        WIP

        :param tile_pos: Destination
        :type speed: int
        :return:
        """
        pass

    def move_by_path(self):
        """
        This method will ensure movement will happen until the player
        reaches its destination
        """
        # TODO maybe this function could be organized better
        if self.path and not self.moving:
            # get the next step of the _plan
            next_plan_step = self.path[len(self.path) - 1]
            # round self.tile_pos
            my_tile_pos = nearest(self.tile_pos)
            # make sure it's adjacent to current location
            adj_x = abs(int(round(my_tile_pos[0])) - int(round(next_plan_step[0]))) == 1
            adj_y = abs(int(round(my_tile_pos[1])) - int(round(next_plan_step[1]))) == 1
            # do xor to invalidate diagonal adjacency
            if (adj_x and not adj_y) or (not adj_x and adj_y):
                # adjacent is true, so execute move to next _plan step
                # get direction we need to move
                if my_tile_pos[0] > next_plan_step[0]:
                    self.move_one_tile("left")
                elif my_tile_pos[0] < next_plan_step[0]:
                    self.move_one_tile("right")
                elif my_tile_pos[1] < next_plan_step[1]:
                    self.move_one_tile("down")
                elif my_tile_pos[1] > next_plan_step[1]:
                    self.move_one_tile("up")
                self.path.pop()  # only pop if we have already executed a move
            if my_tile_pos == next_plan_step:
                # somehow we are already at the next _plan step, just pop
                self.path.pop()
        else:
            logger.debug("self.path=" + str(len(self.path)) + ", self.moving=" + str(self.moving))

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

        position = self.position2 - (0, self.playerHeight // 2)

        return [(get_frame(frame_dict, state), position, 2)]

    def get_collision_dict(self, game):
        """Checks for collision tiles around the player.

        :param game: The Tuxemon game instance itself.

        :type game: tuxemon.Game

        :rtype: Dictionary
        :returns: A dictionary of collision tiles around the player

        """
        collision_dict = {}

        # Create a temporary set of tile coordinates for NPCs. We'll use this to check for
        # collisions.
        npc_positions = set()

        # Get all the NPC's tile positions so we can check for collisions
        for npc in game.npcs.values():
            npc_positions.add(nearest(npc.tile_pos))

        # Combine our map collision tiles with our npc collision
        for pos in npc_positions:
            collision_dict[pos] = "None"

        for tile in game.collision_map:
            collision_dict[tile] = game.collision_map[tile]

        return collision_dict

    def collision_check(self, player_tile_pos, collision_dict, collision_lines_map):
        """Checks collision tiles around the player.

        :param player_pos: An (x, y) list of the player's current tile position. Must be an
            integer.
        :param collision_dict: A dictionary object of (x, y) coordinates that are collidable.

        :type player_pos: List
        :type collision_dict: Dictionary

        :rtype: List
        :returns: A list indicating what tiles relative to the player are collision tiles.
            e.g. ["down", "up"]

        """
        collisions = []

        current_pos = (player_tile_pos[0], player_tile_pos[1])
        down_tile = (player_tile_pos[0], player_tile_pos[1] + 1)
        up_tile = (player_tile_pos[0], player_tile_pos[1] - 1)
        left_tile = (player_tile_pos[0] - 1, player_tile_pos[1])
        right_tile = (player_tile_pos[0] + 1, player_tile_pos[1])

        # Check if the players current position has any limitations.
        if current_pos in collision_dict and collision_dict[current_pos] != "None":
            if not "down" in collision_dict[current_pos]["exit"]:
                collisions.append("down")
            if not "up" in collision_dict[current_pos]["exit"]:
                collisions.append("up")
            if not "left" in collision_dict[current_pos]["exit"]:
                collisions.append("left")
            if not "right" in collision_dict[current_pos]["exit"]:
                collisions.append("right")

        # Check to see if the tile below the player is a collision tile.
        if down_tile in collision_dict:
            if collision_dict[down_tile] != "None":  # Used for conditional collision zones
                if not "up" in collision_dict[down_tile]['enter']:
                    collisions.append("down")
            else:
                collisions.append("down")

        # Check to see if the tile above the player is a collision tile.
        if up_tile in collision_dict:
            if collision_dict[up_tile] != "None":  # Used for conditional collision zones
                if not "down" in collision_dict[up_tile]['enter']:
                    collisions.append("up")
            else:
                collisions.append("up")

        # Check to see if the tile to the left of the player is a collision tile.
        if left_tile in collision_dict:
            if collision_dict[left_tile] != "None":  # Used for conditional collision zones
                if not "right" in collision_dict[left_tile]['enter']:
                    collisions.append("left")
            else:
                collisions.append("left")

        # Check to see if the tile to the right of the player is a collision tile.
        if right_tile in collision_dict:
            if collision_dict[right_tile] != "None":  # Used for conditional collision zones
                if not "left" in collision_dict[right_tile]['enter']:
                    collisions.append("right")
            else:
                collisions.append("right")

        # From the players current tile, check to see if any nearby tile
        # is separated by a wall
        for tile, direction in collision_lines_map:
            if player_tile_pos == tile:
                collisions.append(direction)

        # Return a list of all the collision tiles around the player.
        return collisions

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

    def pathfind(self, dest, game):
        # first check npc doesn't already have a path
        if not self.path:
            # will generate a path and store it in
            # player.path
            starting_loc = nearest(self.tile_pos)

            pathnode = self.pathfind_r(dest,
                                       [PathfindNode(starting_loc)],  # queue
                                       [],  # visited
                                       0,  # depth (not a limit, just a counter)
                                       game)
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
                self.path = path
            else:
                # TODO get current map name for a more useful error
                logger.error("Pathfinding failed to find a path from " +
                             str(starting_loc) + " to " + str(dest) +
                             ". Are you sure that an obstacle-free path exists?")

    def pathfind_r(self, dest, queue, visited, depth, game):
        # recursive breadth first search algorithm

        if not queue:
            # does reaching this case mean we exhausted the search? I think so
            # which means there is no possible path
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
            for adj_pos in self.get_adjacent_tiles(next_node.get_value(), game):
                if adj_pos not in visited and adj_pos not in map(lambda x: x.get_value(), queue):
                    queue = [PathfindNode(adj_pos, next_node)] + queue
                    visited = [next_node.get_value()] + visited

            # recur
            path = self.pathfind_r(dest, queue, visited, depth + 1, game)
            return path

    def get_adjacent_tiles(self, curr_loc, game):
        player_tile_x, player_tile_y = nearest(game.player1.tile_pos)
        collision_map = dict(world.collision_map)
        collision_map[(player_tile_x, player_tile_y)] = "None"
        blocked_directions = self.collision_check(curr_loc, collision_map, world.collision_lines_map)
        adj_tiles = []
        curr_loc = (int(round(curr_loc[0])), int(round(curr_loc[1])))
        if "up" not in blocked_directions:
            adj_tiles.append((curr_loc[0], curr_loc[1] - 1))
        if "down" not in blocked_directions:
            adj_tiles.append((curr_loc[0], curr_loc[1] + 1))
        if "left" not in blocked_directions:
            adj_tiles.append((curr_loc[0] - 1, curr_loc[1]))
        if "right" not in blocked_directions:
            adj_tiles.append((curr_loc[0] + 1, curr_loc[1]))
        return adj_tiles


class Npc(Player):
    def __init__(self, *args, **kwargs):
        super(Npc, self).__init__(*args, **kwargs)

        self.behavior = "wander"
        self.isplayer = False
        self.update_location = False

        # These attributes are used with the new movement system
        self.walkrate = .635  # Tiles per second walk rate
        self.runrate = 1.41  # Tiles per second run rate
        self.moverate = self.walkrate

        # scale them?
        self.walkrate *= prepare.SCALE
        self.runrate *= prepare.SCALE
        self.moverate = self.walkrate

        self.tile_destination = [0, 0]
        self.current_tile = [0.0, 0.0]
        self.running = False
        self.interactions = []  # List of ways player can interact with the Npc

    def move(self, tile_size, time_passed_seconds, game):

        # Create a temporary set of tile coordinates for NPCs. We'll use this to check for
        # collisions.
        npc_positions = set()
        collision_dict = {}

        # Get all the NPC's tile monsters_in_play so we can check for collisions.
        for npc in game.npcs.values():
            npc_pos = nearest(npc.tile_pos)
            npc_positions.add(npc_pos)

        # Make sure the NPC doesn't collide with the player too.
        player_pos_x = int(round(game.player1.tile_pos[0]))
        player_pos_y = int(round(game.player1.tile_pos[1]))
        npc_positions.add((player_pos_x, player_pos_y))

        # Combine our map collision tiles with our npc collision monsters_in_play
        for pos in npc_positions:
            collision_dict[pos] = "None"

        for tile in game.collision_map:
            collision_dict[tile] = game.collision_map[tile]

        self._continue_move()
        self._check_move(collision_dict, game)


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
