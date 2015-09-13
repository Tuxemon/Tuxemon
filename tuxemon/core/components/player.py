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
#
#
# core.components.player Player module.
#
#

import logging
import pygame
import pprint
import time
from . import pyganim
from . import ai
from . import config

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.player successfully imported")

# Class definition for the player.
class Player(object):
    """A class for a player object. This object can be used for NPCs as well as the player:
    
    Example:

    >>> player1 = core.components.player.Player()
    >>> # Scale the sprite and its animations
    >>> for key, animation in player1.sprite.items():
    ...     animation.scale(tuple(i * scale for i in animation.getMaxSize()))
    ...
    >>> for key, image in player1.standing.items():
    ...     player1.standing[key] = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
    ...
    >>> # Set the walking and running pixels per second based on the scale
    >>> player1.walkrate *= scale
    >>> player1.runrate *= scale


    """
    def __init__(self, sprite_name="player", name="Red"):
        self.name = name			# This is the player's name to be used in dialog
        self.ai = None              # Whether or not this player has AI associated with it
        self.sprite = {}			# The pyganim object that contains the player animations

        # Get all of the player's standing animation images.
        self.standing = {}
        standing_types = ["front", "back", "left", "right"]
        for standing_type in standing_types:
            surface = pygame.image.load('resources/sprites/%s_%s.png' % (sprite_name, standing_type)).convert_alpha()
            surface_top = surface.subsurface((0, 0,
                                              surface.get_width(), int(surface.get_height() / 2)))
            surface_bottom = surface.subsurface((0, int(surface.get_height() / 2),
                                                 surface.get_width(), int(surface.get_height() / 2)))
            self.standing[standing_type] = surface
            self.standing[standing_type + "-top"] = surface_top
            self.standing[standing_type + "-bottom"] = surface_bottom

        self.playerWidth, self.playerHeight = self.standing["front"].get_size()    # The player's sprite size in pixels
        self.inventory = {}			# The Player's inventory.
        self.monsters = []			# This is a list of tuxemon the player has
        self.party_limit = 6        # The maximum number of tuxemon this player can hold
        self.walking = False			# Whether or not the player is walking
        self.running = False			# Whether or not the player is running
        self.moving = False			# Whether or not the player is moving
        self.move_direction = "down"		# This is a string of the direction we're moving if we're in the middle of moving
        self.direction = {"up": False, "down": False, "left": False, "right": False}	# What direction the player is moving
        self.facing = "down"	# What direction the player is facing
        self.walkrate = 60			# The rate in pixels per second the player is walking
        self.runrate = 118			# The rate in pixels per second the player is running
        self.moverate = self.walkrate		# The movement rate in pixels per second
        self.position = [0,0]			# The player's sprite position on the screen
        self.global_pos = [0,0]			# This is the offset we're going to add to the x,y coordinates of everything on the map
        self.tile_pos = (0,0)       # This is the position of the player based on tile
        self.tile_size = [16,16]
        self.move_destination = [0,0]		# The player's destination location to move to
        #self.colliding = False			# To check and see if we're colliding with anything
        self.rect = pygame.Rect(self.position[0], self.position[1], self.playerWidth, self.playerHeight) # Collision rect
        self.game_variables = {}		# Game variables for use with events

        self.path = None
        
        # Load all of the player's sprite animations
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images_and_durations = [('resources/sprites/%s_%s.%s.png' % (sprite_name, anim_type, str(num).rjust(3, '0')), 
                                    config.Config().player_animation_speed) for num in range(4)]

            # Loop through all of our animations and get the top and bottom subsurfaces.
            top_frames = []
            bottom_frames = []
            for frame in images_and_durations:
                # Load the frame image
                surface = pygame.image.load(frame[0]).convert_alpha()
                top_surface = surface.subsurface((0, 0,
                                                  surface.get_width(), surface.get_height() / 2))
                bottom_surface = surface.subsurface((0, surface.get_height() / 2,
                                                     surface.get_width(), surface.get_height() / 2))
                top_frames.append((top_surface, frame[1]))
                bottom_frames.append((bottom_surface, frame[1]))

            # Create an animation set for the top and bottom halfs of our sprite, so we can draw
            # them on different layers.
            self.sprite[anim_type] = pyganim.PygAnimation(images_and_durations)
            self.sprite[anim_type + '-top'] = pyganim.PygAnimation(top_frames)
            self.sprite[anim_type + '-bottom'] = pyganim.PygAnimation(bottom_frames)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animtion
        # objects at the same time, so that way they'll always be in sync with each
        # other.
        self.moveConductor = pyganim.PygConductor(self.sprite)
        self.moveConductor.play()


    def move(self, screen, tile_size, time_passed_seconds, (global_x, global_y), game):
        """Draws text to the current menu object
        
        :param screen: The pygame surface you wish to blit the player onto.
        :param tile_size: A list with the [width, height] of the tiles in pixels. This is used for
            tile-based movement.
        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.
        :param global_x/global_y: The global_x/y variables that we add to everything on a map
            to move everything around the player.
        :param game: The Tuxemon game instance itself.
        
        :type screen: pygame.Surface
        :type tile_size: List
        :type time_passed_seconds: Float
        :type global_x/global_y: Tuple
        :type game: tuxemon.Game

        :rtype: Tuple
        :returns: The updated (global_x, global_y) coordinates after moving (or stopping due
            to collision)
        
        """

        # Create a temporary set of tile coordinates for NPCs. We'll use this to check for
        # collisions.
        npc_positions = set()
        
        # Get all the NPC's tile positions so we can check for collisions.
        for npc in game.npcs:
            npc_pos_x = int(round(npc.tile_pos[0]))
            npc_pos_y = int(round(npc.tile_pos[1]))
            npc_positions.add( (npc_pos_x, npc_pos_y) )
        
        # Combine our map collision tiles with our npc collision positions
        collision_set = game.collision_map.union(npc_positions)
            
        # Round the player's tile position to an integer value. We test for collisions based on
        # an integer value.
        player_pos = ( int(round(self.tile_pos[0])), int(round(self.tile_pos[1])) )
        
            
        # *** Here we're continuing a move if we're in the middle of one already *** #
        # If the player is in the middle of moving and facing a certain direction, move in that
        # direction
        if self.move_direction == "up" and self.moving:
            # If we've reached our destination and are no longer holding an arrow key, set moving
            # to false and set the position to the destination
            if global_y >= self.move_destination[1] and not self.direction["up"]:  # self.direction means that arrow key is being held
                self.moving = False
                global_y = self.move_destination[1]	# Set it to the destination so we don't overshoot it

            # If we're already in the middle of walking and we haven't reached the tile, THEN
            # KEEP WALKING DAMNIT
            else:
                global_y += int((self.moverate * time_passed_seconds))

                # If we're holding down the arrow key and we overshoot our original destination,
                # set our next destination tile and see if we'll collide with it or not.
                if global_y >= self.move_destination[1] and self.direction["up"]:

                    # If the destination tile won't collide with anything, then proceed with moving.
                    if not "up" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "up"

                        # Set the destination position we'd wish to reach if we just started walking.
                        self.move_destination = [int(self.move_destination[0]), int(self.move_destination[1] + tile_size[1])]
                        

                    # If we are going to collide with something, set our position to the original
                    # move destination and stop moving
                    else:
                        self.moving = False
                        global_y = self.move_destination[1]

    
        if self.move_direction == "down" and self.moving:
            if global_y <= self.move_destination[1] and not self.direction["down"]:
                self.moving = False
                global_y = self.move_destination[1]	# Set it to the destination so we don't overshoot it

            else:
                global_y -= int((self.moverate * time_passed_seconds))

                if global_y <= self.move_destination[1] and self.direction["down"]:

                    if not "down" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "down"

                        self.move_destination = [int(self.move_destination[0]),
                                                 int(self.move_destination[1] - tile_size[1])]

                    else:
                        self.moving = False
                        global_y = self.move_destination[1]

    
        if self.move_direction == "left" and self.moving:
            if global_x >= self.move_destination[0] and not self.direction["left"]:
                self.moving = False
                global_x = self.move_destination[0]	# Set it to the destination so we don't overshoot it
            else:
                global_x += int((self.moverate * time_passed_seconds))

                if global_x >= self.move_destination[0] and self.direction["left"]:

                    if not "left" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                         self.moving = True
                         self.move_direction = "left"

                         self.move_destination = [int(self.move_destination[0] + tile_size[1]),
                                                  int(self.move_destination[0])]

                    else:
                         self.moving = False
                         global_x = self.move_destination[0]

    
        if self.move_direction == "right" and self.moving:
            if global_x <= self.move_destination[0] and not self.direction["right"]:
                self.moving = False
                global_x = self.move_destination[0]	# Set it to the destination so we don't overshoot it
            else:
                global_x -= int((self.moverate * time_passed_seconds))

                if global_x <= self.move_destination[0] and self.direction["right"]:

                    if not "right" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "right"

                        self.move_destination = [int(self.move_destination[0] - tile_size[1]),
                                                 int(self.move_destination[0])]

                    else:
                        self.moving = False
                        global_x = self.move_destination[0]


        # *** Here we're playing the animation and setting a new destination if we currently don't have one. *** #
        # player.direction is set when a key is pressed. player.moving is set when we're still in
        # the middle of a move
        if self.direction["up"] or self.direction["down"] or self.direction["left"] or self.direction["right"]:
            # If we've pressed any arrow key, play the move animations
            self.moveConductor.play()

            # If we pressed an arrow key and we're not currently moving, set a new tile destination
            if self.direction["up"]:
                if not self.moving:
                    # Set the destination position we'd wish to reach if we just started walking.
                    self.move_destination = [int(global_x), int(global_y + tile_size[1])]

                    # If the destination tile won't collide with anything, then proceed with moving.
                    if not "up" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "up"

            elif self.direction["down"]:
                if not self.moving:
                    # Set the destination position we'd wish to reach if we just started walking.
                    self.move_destination = [int(global_x), int(global_y - tile_size[1])]

                    if not "down" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "down"

            elif self.direction["left"]:
                if not self.moving:
                    # Set the destination position we'd wish to reach if we just started walking.
                    self.move_destination = [int(global_x + tile_size[1]), int(global_y)]

                    if not "left" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "left"

            elif self.direction["right"]:
                if not self.moving:
                    # Set the destination position we'd wish to reach if we just started walking.
                    self.move_destination = [int(global_x - tile_size[1]), int(global_y)]

                    if not "right" in self.collision_check(player_pos, collision_set, game.collision_lines_map):
                        self.moving = True
                        self.move_direction = "right"


        # If we're not holding down an arrow key and the player is not moving, stop the animation
        # and draw the standing gfx
        else:
            if not self.moving:
                self.moveConductor.stop()

        return global_x, global_y

    def move_one_tile(self, direction):
        # moves one tile in the given direction
        
        # start moving if we aren't moving
        if not self.moving:
            if direction == "up":
                self.tile_move_dest = (self.tile_pos[0], self.tile_pos[1]-1)
                self.moving = True
                self.move_direction = "up"
            elif direction == "down":
                self.tile_move_dest = (self.tile_pos[0], self.tile_pos[1]+1)
                self.moving = True
                self.move_direction = "down"
            elif direction == "left":
                self.tile_move_dest = (self.tile_pos[0]-1, self.tile_pos[1])
                self.moving = True
                self.move_direction = "left"
            elif direction == "right":
                self.tile_move_dest = (self.tile_pos[0]+1, self.tile_pos[1])
                self.moving = True
                self.move_direction = "right"
            else:
                logger.error("In player.move_one_tile() direction is not up,down,left,right")
                
        # if we are moving, see if we have reached our destination
        if self.moving:
            if self.tile_pos == self.tile_move_dest:
                self.moving = False

    def move_by_path(self):
        '''
        This method will ensure movement will happen until the player
        reaches its destination
        '''
        # TODO maybe this function could be organized better
        if self.path:
            # get the next step of the plan
            next_plan_step = self.path.pop(0)
            # make sure it's adjacent to current location
            adj_x = abs(self.tile_pos[0] - next_plan_step[0]) == 1
            adj_y = abs(self.tile_pos[1] - next_plan_step[1]) == 1
            # do xor to invalidate diagonal adjacency
            if (adj_x and not adj_y) or (not adj_x and adj_y):
                # adjacent is true, so execute move to next plan step
                # get direction we need to move
                if self.tile_pos[0] > next_plan_step[0]:
                    self.move_one_tile("left")
                elif self.tile_pos[0] < next_plan_step[0]:
                    self.move_one_tile("right")
                elif self.tile_pos[1] < next_plan_step[1]:
                    self.move_one_tile("down")
                elif self.tile_pos[1] > next_plan_step[1]:
                    self.move_one_tile("up")


    def draw(self, screen, layer):
        """Draws the player to the screen depending on whether or not they are moving or
        standing still.

        :param screen: The pygame screen to draw the player to.
        :param layer: Which part of the sprite to draw. Can be "top" or "bottom"

        :type screen: pygame.Surface
        :type layer: String

        :returns: None

        """

        # If this is the bottom half, we need to draw it at a lower position.
        if layer == "bottom":
            offset = self.standing["front"].get_height() / 2
        else:
            offset = 0

        # If the player is moving, draw its movement animation.
        if self.move_direction == "up" and self.moving:
            self.sprite["back_walk-" + layer].blit(screen, (self.position[0],
                                                            self.position[1] + offset))
        elif self.move_direction == "down" and self.moving:
            self.sprite["front_walk-" + layer].blit(screen, (self.position[0],
                                                             self.position[1] + offset))
        elif self.move_direction == "left" and self.moving:
            self.sprite["left_walk-" + layer].blit(screen, (self.position[0],
                                                            self.position[1] + offset))
        elif self.move_direction == "right" and self.moving:
            self.sprite["right_walk-" + layer].blit(screen, (self.position[0],
                                                             self.position[1] + offset))

        # If the player is not moving, draw its standing animation.
        if not self.moving:
            if self.facing == "up":
                screen.blit(self.standing["back-" + layer], (self.position[0],
                                                             self.position[1] + offset))
            if self.facing == "down":
                screen.blit(self.standing["front-" + layer], (self.position[0],
                                                              self.position[1] + offset))
            if self.facing == "left":
                screen.blit(self.standing["left-" + layer], (self.position[0],
                                                             self.position[1] + offset))
            if self.facing == "right":
                screen.blit(self.standing["right-" + layer], (self.position[0],
                                                              self.position[1] + offset))


    def collision_check(self, player_tile_pos, collision_set, collision_lines_map):
        """Checks collision tiles around the player.

        :param player_pos: An (x, y) list of the player's current tile position. Must be an
            integer.
        :param collision_set: A set() object of (x, y) coordinates that are collidable.
        
        :type player_pos: List
        :type collision_set: Set

        :rtype: List
        :returns: A list indicating what tiles relative to the player are collision tiles.
            e.g. ["down", "up"]
        
        """
        
        collisions = []
        
        # Check to see if the tile below the player is a collision tile.
        if (player_tile_pos[0], player_tile_pos[1] + 1) in collision_set:
            collisions.append("down")
        
        # Check to see if the tile above the player is a collision tile.
        if (player_tile_pos[0], player_tile_pos[1] - 1) in collision_set:
            collisions.append("up")

        # Check to see if the tile to the left of the player is a collision tile.
        if (player_tile_pos[0] - 1, player_tile_pos[1]) in collision_set:
            collisions.append("left")

        # Check to see if the tile to the right of the player is a collision tile.
        if (player_tile_pos[0] + 1, player_tile_pos[1]) in collision_set:
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
        will send the monster to PC archive.

        :param monster: The core.components.monster.Monster object to add to the player's party.
        
        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None
        
        """
        
        if len(self.monsters) >= self.party_limit:
            print "Send to PC"
            
        else:
            self.monsters.append(monster)
        
        
    def remove_monster(self, monster):
        """Removes a monster from this player's party.

        :param monster: The core.components.monster.Monster object to remove from the player's
            party.
        
        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None
        
        """
        
        # Remove the tuxemon if they are in this player's party
        if monster in self.monsters:
            self.monsters.remove(monster)

    def switch_monsters(self, index_monster_1, index_monster_2):
        """Swap two monsters in this player's party
        
        :param index_monster_1/index_monster_2: The indexes of the monsters to switch in the player's party.
        
        :type index_monster_1/index_monster_2: int
        
        :rtype: None
        :returns: None
        
        """
        
        # Swap the tuxemons if they are in the player's party
        if index_monster_1 < len(self.monsters) and index_monster_2 < len(self.monsters):
            self.monsters[index_monster_1], self.monsters[index_monster_2] = self.monsters[index_monster_2], self.monsters[index_monster_1]
        
    def scale_sprites(self, scale):
        # Scale the sprite and its animations
        for key, animation in self.sprite.items():
            animation.scale(
                tuple(i * scale for i in animation.getMaxSize()))

        for key, image in self.standing.items():
            self.standing[key] = pygame.transform.scale(
                image, (image.get_width() * scale,
                        image.get_height() * scale))

    def pathfind(self, dest, game):
        # first check npc doesn't already have a path
        if not self.path:

            # will generate a path and store it in 
            # player.path
            starting_loc = (int(round(self.tile_pos[0])),
                            int(round(self.tile_pos[1])))
            
            pathnode = self.pathfind_r(dest, 
                                   [PathfindNode(starting_loc)], # queue
                                   [], # visited
                                   0,  # depth (not a limit, just a counter)
                                   game)
            if pathnode:
                # traverse the node to get the path
                path = []
                while pathnode:
                    path.append(pathnode.get_value())
                    pathnode = pathnode.get_parent()
                # store the path
                self.path = path 
            else:
                # TODO get current map name for a more useful error
                logger.error("Pathfinding failed to find a path from " + 
                             str(starting_loc) + " to " + str(dest) + 
                             ". Are you sure that an obstacle-free path exists?")
            
    def pathfind_r(self, dest, queue, visited, depth, game):
        # recursive breadth first search algorithm        

        if len(queue) == 0:
            # does reaching this case mean we exhausted the search? I think so
            # which means there is no possible path
            return False

        elif queue[0].get_value() == dest:
            # done
            return queue[0]

        else:
            # pop next tile off queue
            next_node = queue.pop(0)

            # add neighbors of current tile to queue
            # if we haven't checked them already
            for adj_pos in self.get_adjacent_tiles(next_node.get_value(), game):
                if adj_pos not in visited and adj_pos not in map(lambda x: x.get_value(), queue):
                    queue = [PathfindNode(adj_pos,next_node)]+queue
                    visited = [next_node.get_value()]+visited

            # recur
            path = self.pathfind_r(dest,queue,visited,depth+1,game)
            #print "path is: " + str(path)
            return path
            
    def get_adjacent_tiles(self, curr_loc, game):
        # Get a copy of the world state.
        world = game.state_dict["WORLD"]
        blocked_directions = self.collision_check(curr_loc, world.collision_map, world.collision_lines_map)
        adj_tiles = []
        curr_loc = (int(round(curr_loc[0])),int(round(curr_loc[1])))
        if "up" not in blocked_directions:
            adj_tiles.append((curr_loc[0],curr_loc[1]-1))
        if "down" not in blocked_directions:
            adj_tiles.append((curr_loc[0],curr_loc[1]+1))
        if "left" not in blocked_directions:
            adj_tiles.append((curr_loc[0]-1,curr_loc[1]))
        if "right" not in blocked_directions:
            adj_tiles.append((curr_loc[0]+1,curr_loc[1]))        
        return adj_tiles

class Npc(Player):
    def __init__(self, sprite_name="maple", name="Maple"):

        # Initialize the parent menu class's default shit
        Player.__init__(self, sprite_name, name)

        self.name = name
        self.behavior = "wander"

    
class PathfindNode():
    '''
    Used in path finding search
    '''
    def __init__(self, value, parent=None):
        self.parent = parent
        self.value = value

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent

    def get_value(self):
        return self.value
    
    def __str__(self):
        s = str(self.value)
        if self.parent != None:
            s += str(self.parent)
        return s

        
