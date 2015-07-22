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

from core.components import pyganim
from core.components import ai
from core.components import config

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
    def __init__(self, sprite_name="player", name="Red", ai=None):
        self.name = name
        self.ai = ai
        self.sprite = {"name": sprite_name}

        self.width = 1
        self.height = 2
        self.x = 0.0
        self.y = 0.0

        self.inventory = {}
        self.monsters = []

        self.facing = "down"
        self.running = False
        self.moving = False
        self.move_direction = "down"
        self.direction = {"up": False,
                          "down": False,
                          "left": False,
                          "right": False}
        self.walkrate = 1.0
        self.runrate = 2.0
        self.moverate = self.walkrate
        self.move_destination = [0, 0]

        self.game_variables = {}


    def load_sprite(self):
        # Get all of the player's standing animation images.
        self.sprite['standing'] = {}
        standing_types = ["front", "back", "left", "right"]
        for standing_type in standing_types:
            surface = pygame.image.load('resources/sprites/%s_%s.png' % 
                (self.sprite['name'], standing_type)).convert_alpha()
            surface_top = surface.subsurface((0, 0,
                                              surface.get_width(), int(surface.get_height() / 2)))
            surface_bottom = surface.subsurface((0, int(surface.get_height() / 2),
                                                 surface.get_width(), int(surface.get_height() / 2)))
            self.sprite['standing'][standing_type] = surface
            self.sprite['standing'][standing_type + "-top"] = surface_top
            self.sprite['standing'][standing_type + "-bottom"] = surface_bottom

        # Load all of the player's sprite animations
        self.sprite['walking'] = {}
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images_and_durations = [('resources/sprites/%s_%s.%s.png' % (self.sprite['name'], anim_type, str(num).rjust(3, '0')), 
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
            self.sprite['walking'][anim_type] = pyganim.PygAnimation(images_and_durations)
            self.sprite['walking'][anim_type + '-top'] = pyganim.PygAnimation(top_frames)
            self.sprite['walking'][anim_type + '-bottom'] = pyganim.PygAnimation(bottom_frames)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animtion
        # objects at the same time, so that way they'll always be in sync with each
        # other.
        self.move_conductor = pyganim.PygConductor(self.sprite['walking'])
        self.move_conductor.play()


    def move(self, direction, game):
        """Moves our player in a particular direction.
        
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

        # If we're already moving, don't do anything.
        if self.moving:
            return

        # Create a temporary set of tile coordinates for NPCs. We'll use this to check for
        # collisions.
        npc_positions = set()
        
        # Get all the NPC's tile positions so we can check for collisions.
        for npc in game.npcs:
            npc_pos_x = int(round(npc.tile_pos[0]))
            npc_pos_y = int(round(npc.tile_pos[1]))
            npc_positions.add((npc_pos_x, npc_pos_y))
        
        # Combine our map collision tiles with our npc collision positions
        collision_set = game.collision_map.union(npc_positions)
            
        # Round the player's tile position to an integer value. We test for collisions based on
        # an integer value.
        player_position = (int(round(self.x)), int(round(self.y)))
        
        # Here we're playing the animation and setting a new destination if
        # we currently don't have one. player.direction is set when a key is
        # pressed. player.moving is set when we're still in the middle of a move.
        if self.direction["up"] or self.direction["down"] or self.direction["left"] or self.direction["right"]:
            # If we've pressed any arrow key, play the move animations
            if self.sprite:
                self.move_conductor.play()

            # If we pressed an arrow key and we're not currently moving, set a new tile destination
            if self.direction["up"]:
                self.move_destination = [player_position[0], player_position[1] + 1]
                if not "up" in self.collision_check(player_position, collision_set):
                    self.move_direction = "up"
                    self.moving = True

            elif self.direction["down"]:
                self.move_destination = [player_position[0], player_position[1] - 1]
                if not "down" in self.collision_check(player_position, collision_set):
                    self.move_direction = "up"
                    self.moving = True
                self.move_direction = "down"
                self.moving = True

            elif self.direction["left"]:
                self.move_destination = [player_position[0] - 1, player_position[1]]
                if not "left" in self.collision_check(player_position, collision_set):
                    self.move_direction = "left"
                    self.moving = True

            elif self.direction["right"]:
                self.move_destination = [player_position[0] + 1, player_position[1]]
                if not "right" in self.collision_check(player_position, collision_set):
                    self.move_direction = "right"
                    self.moving = True


    def update(self, time_passed_seconds, game):
        # *** Here we're continuing a move it we're in the middle of one already *** #
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
                    if not "up" in self.collision_check(player_pos, collision_set):
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

                    if not "down" in self.collision_check(player_pos, collision_set):
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

                    if not "left" in self.collision_check(player_pos, collision_set):
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

                    if not "right" in self.collision_check(player_pos, collision_set):
                        self.moving = True
                        self.move_direction = "right"

                        self.move_destination = [int(self.move_destination[0] - tile_size[1]),
                                                 int(self.move_destination[0])]

                    else:
                        self.moving = False
                        global_x = self.move_destination[0]


        pass


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


    def collision_check(self, player_tile_pos, collision_set):
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
        
        if len(self.monsters) >= prepare.PARTY_LIMIT:
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



class Npc(Player):
    def __init__(self, sprite_name="maple", name="Maple"):

        # Initialize the parent menu class's default shit
        Player.__init__(self, sprite_name, name)

        self.name = name
        self.behavior = "wander"



