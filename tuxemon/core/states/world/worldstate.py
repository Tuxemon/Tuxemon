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
# core.states.world Handles the world map and player movement.
#
#
from __future__ import division

# Import various python libraries
import logging
import math
import itertools

import pygame

# Import Tuxemon internal libraries
from core import prepare
from core import state
from core import tools
from core.components import map
from core.components import networking

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class WorldState(state.State):
    """ The state responsible for the world game play
    """

    def startup(self):
        # Provide access to the screen surface
        self.screen = self.game.screen
        self.screen_rect = prepare.SCREEN_RECT

        # Set the native tile size so we know how much to scale
        self.tile_size = prepare.TILE_SIZE

        # Set the status icon size so we know how much to scale
        self.icon_size = prepare.ICON_SIZE

        # Get the screen's resolution
        self.resolution = prepare.SCREEN_SIZE

        # Native resolution is similar to the old gameboy resolution. This is
        # used for scaling.
        self.native_resolution = prepare.NATIVE_RESOLUTION

        # Set the world's current state. This is used for various functions.
        self.state = "WorldState"

        ######################################################################
        #                          Event Engine                              #
        ######################################################################

        # Get a copy of the event engine from core.control.Control.
        self.event_engine = self.game.event_engine

        ######################################################################
        #                              Map                                   #
        ######################################################################

        # Set the tiles and map size variables
        self.tiles = []
        self.map_size = []

        # Find out how many tiles can fit on the visible screen. We use this
        # so we draw only the tiles that are visible.
        self.visible_tiles = [
            int(math.ceil(self.resolution[0] / self.tile_size[0]) + 1),
            int(math.ceil(self.resolution[1] / self.tile_size[1]) + 1)]
        # self.visible_tiles = [5, 5]

        # load the starting map
        map_name = prepare.BASEDIR + "resources/maps/%s" % prepare.CONFIG.starting_map
        self.change_map(map_name)

        ######################################################################
        #                           Player Details                           #
        ######################################################################

        self.player1 = prepare.player1
        self.npcs = []
        self.npcs_off_map = []
        self.wants_duel = False

        # Set the global coordinates used to pan the screen.
        self.start_position = prepare.CONFIG.starting_position
        self.global_x = self.player1.position[0] - \
            (self.start_position[0] * self.tile_size[0])
        self.global_y = self.player1.position[1] - \
            (self.start_position[1] * self.tile_size[1]) + self.tile_size[0]

        ######################################################################
        #                            Transitions                             #
        ######################################################################

        # defaults variables for transition
        self.SAVE_THIS_FUCKING_SCREEN = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_alpha = 0
        self.start_transition = False
        self.start_transition_back = False
        self.black_screen = 0

        # The delayed teleport variable is used to perform a teleport in the
        # middle of a transition. For example, fading to black, then
        # teleporting the player, and fading back in again.
        self.delayed_teleport = False

        # The delayed facing variable used to change the player's facing in
        # the middle of a transition.
        self.delayed_facing = None

        ######################################################################
        #                          Collision Map                             #
        ######################################################################

        # If we want to display the collision map for debug purposes
        if prepare.CONFIG.collision_map == "1":
            # For drawing the collision map
            self.collision_tile = pygame.Surface(
                (self.tile_size[0], self.tile_size[1]))
            self.collision_tile.set_alpha(128)
            self.collision_tile.fill((255, 0, 0))

        ######################################################################
        #                       Fullscreen Animations                        #
        ######################################################################

        # The cinema bars are used for cinematic moments.
        # The cinema state can be: "off", "on", "turning on" or "turning off"
        self.cinema_state = "off"
        self.cinema_speed = 15 * prepare.SCALE    # Pixels per second speed of the animation.

        self.cinema_top = {}
        self.cinema_bottom = {}

        # Create a surface that we'll use as black bars for a cinematic
        # experience
        self.cinema_top['surface'] = pygame.Surface(
            (self.resolution[0], self.resolution[1] / 6))
        self.cinema_bottom['surface'] = pygame.Surface(
            (self.resolution[0], self.resolution[1] / 6))

        # Fill our empty surface with black
        self.cinema_top['surface'].fill((0, 0, 0))
        self.cinema_bottom['surface'].fill((0, 0, 0))

        # When cinema mode is off, this will be the position we'll draw the
        # black bar.
        self.cinema_top['off_position'] = [
            0, -self.cinema_top['surface'].get_height()]
        self.cinema_bottom['off_position'] = [0, self.resolution[1]]
        self.cinema_top['position'] = list(self.cinema_top['off_position'])
        self.cinema_bottom['position'] = list(
            self.cinema_bottom['off_position'])

        # When cinema mode is ON, this will be the position we'll draw the
        # black bar.
        self.cinema_top['on_position'] = [0, 0]
        self.cinema_bottom['on_position'] = [
            0, self.resolution[1] - self.cinema_bottom['surface'].get_height()]

    def trigger_fade_in(self):
        """ World state has own fade code b/c moving maps doesn't change state

        :returns: None
        """
        self.transition_time = 1
        self.start_transition_back = True
        self.transition_alpha = 255

    def update(self, time_delta):
        """The primary game loop that executes the world's game functions every frame.

        :param time_delta: Amount of time passed since last frame.

        :type time_delta: Float

        :rtype: None
        :returns: None

        """
        logger.debug("*** Game Loop Started ***")
        logger.debug("Player Variables:" + str(self.player1.game_variables))

        # Get the player's tile position based on the global_x/y variables. Since the player's sprite is 1 x 2
        # tiles in size, we add 1 to the 'y' position so the player's actual position will be on the bottom
        # portion of the sprite.
        self.player1.tile_pos = (float((self.player1.position[0] - self.global_x)) / float(
            self.tile_size[0]), (float((self.player1.position[1] - self.global_y)) / float(self.tile_size[1])) + 1)

    def draw(self, surface):
        self.screen = surface

        # Fill the screen _background with black
        surface.fill((0, 0, 0))

        self.map_drawing(surface)
        self.player_movement()
        self.high_map_drawing(surface)
        self.midscreen_animations(surface)
        self.fullscreen_animations(surface)

    def process_event(self, event):
        """Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        # Handle Key DOWN events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                logger.info("Opening main menu!")
                self.game.push_state("WorldMenuState")

            # If we receive an arrow key press, set the facing and
            # moving direction to that direction
            if event.key == pygame.K_UP:
                self.player1.direction["up"] = True
                self.player1.facing = "up"
            if event.key == pygame.K_DOWN:
                self.player1.direction["down"] = True
                self.player1.facing = "down"
            if event.key == pygame.K_LEFT:
                self.player1.direction["left"] = True
                self.player1.facing = "left"
            if event.key == pygame.K_RIGHT:
                self.player1.direction["right"] = True
                self.player1.facing = "right"
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.check_interactable_space()

        # Handle Key UP events
        if event.type == pygame.KEYUP:
            # If the player lets go of the key, set the moving
            # direction to false
            if event.key == pygame.K_UP:
                self.player1.direction["up"] = False

            if event.key == pygame.K_DOWN:
                self.player1.direction["down"] = False

            if event.key == pygame.K_LEFT:
                self.player1.direction["left"] = False

            if event.key == pygame.K_RIGHT:
                self.player1.direction["right"] = False

        self.game.client.set_key_condition(event)

        # by default, just pass every event down, since we assume
        # that the world state will be the last running state, before
        # the event engine.
        return event

    ####################################################
    #                   Map Drawing                    #
    ####################################################
    def map_drawing(self, surface):
        """Draws the map tiles in a layered order.

        :param: None

        :rtype: None
        :returns: None

        """

        # Reset the higher layer tiles so we can draw them over the player
        self.highlayer_tiles = []
        self.medlayer_tiles = []

        # What region of tiles should be visible?
        left   = -int(self.global_x / self.tile_size[0])
        top    = -int(self.global_y / self.tile_size[1])
        right  = left + self.visible_tiles[0]
        bottom = top + self.visible_tiles[1]

        # Clamp that to the map boundaries.
        left   = max(left, 0)
        top    = max(top, 0)
        right  = min(right, len(self.tiles) - 1)
        bottom = min(bottom, len(self.tiles[0]) - 1)

        # Loop through all visible tiles
        for row in xrange(top, bottom):
            for column in xrange(left, right):
                if self.tiles[column][row]:		# Check to see if a tile exists at this coordinates
                    for tile in self.tiles[column][row]:
                        # Append the high level tiles to its own
                        # list to be drawn over the player. Tiles on layer 4 will be drawn
                        # above the player's body, but below the player's head.
                        if tile["layer"] == 4:
                            self.medlayer_tiles.append(tile)
                        elif tile["layer"] > 4:
                            self.highlayer_tiles.append(tile)
                        else:
                            draw_position = (tile["position"][0] + self.global_x,
                                             tile["position"][1] + self.global_y)
                            if type(tile["surface"]) is pygame.Surface:
                                surface.blit(tile["surface"], draw_position)
                            else:
                                tile["surface"].blit(surface, draw_position)

        # We need to keep track of the global_x/y that we used to draw the bottom tiles so we use
        # the same values for the higher layer tiles. We have to do this because when we draw the
        # player's movement, we modify the global_x/y values to start moving the map.
        self.orig_global_x = self.global_x
        self.orig_global_y = self.global_y

    ####################################################
    #                Player Movement                   #
    ####################################################
    def player_movement(self):
        """Handles player's movement, collision, and drawing. Also draws map
        tiles that are on a layer above the player.

        :param: None

        :rtype: None
        :returns: None

        """
        # Get all the keys pressed for modifiers only!
        pressed = list(pygame.key.get_pressed())
        self.ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        self.alt_held = pressed[pygame.K_LALT] or pressed[pygame.K_RALT]
        self.shift_held = pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]

        # TODO: phase out in favor of a global game clock
        self.time_passed_seconds = self.game.time_passed_seconds

        # Handle tile based movement for the player
        if self.shift_held:
            self.player1.moverate = self.player1.runrate
        else:
            self.player1.moverate = self.player1.walkrate

        # Set the global_x/y when the player moves around
        self.global_x, self.global_y = self.player1.move(
            self.screen, self.tile_size, self.time_passed_seconds, (self.global_x, self.global_y), self)

        # Find out how many pixels we've moved since we started moving
        self.global_x_diff = self.orig_global_x - self.global_x
        self.global_y_diff = self.orig_global_y - self.global_y

        # Draw any game NPC's
        for npc in self.npcs:
            if npc.running:
                npc.moverate = npc.runrate
            else:
                npc.moverate = npc.walkrate
            # Get the NPC's tile position based on his pixel position. Since the NPC's sprite is 1 x 2
            # tiles in size, we add 1 to the 'y' position so the NPC's actual position will be on the bottom
            # portion of the sprite.
            npc.tile_pos = (float((npc.position[0] - self.global_x)) / float(
                self.tile_size[0]), (float((npc.position[1] - self.global_y)) / float(self.tile_size[1])) + 1)

            # If the NPC is not visible on the screen, don't draw him
            #if self.screen_rect.colliderect(npc.rect):
            #    npc.move(self.screen, self.tile_size, self.time_passed_seconds, (     #### Disabled for now
            #        npc.position[0], npc.position[1]), self)

            # Move the NPC with the map as it moves
            npc.position[0] -= self.global_x_diff
            npc.position[1] -= self.global_y_diff

            # debug info
            #print("npc.tile_pos="+str(npc.tile_pos))

            # if the npc has a path, move it along its path
            if npc.path:
                npc.move_by_path()

            npc.move(self.tile_size, self.time_passed_seconds, self)

            # Reset our directions after moving.
            if not npc.isplayer:
                npc.direction["up"] = False
                npc.direction["down"] = False
                npc.direction["left"] = False
                npc.direction["right"] = False

            if npc.update_location:
                char_dict ={"tile_pos": npc.final_move_dest,
                            }
                networking.update_client(npc, char_dict, self.game)
                npc.update_location = False

            # Draw the bottom part of the NPC.
            npc.draw(self.screen, "bottom")

        # Move any multiplayer characters that are off map so we know where they should be when we change maps.
        for npc in self.npcs_off_map:
            if npc.running:
                npc.moverate = npc.runrate
            else:
                npc.moverate = npc.walkrate
            # Get the NPC's tile position based on his pixel position. Since the NPC's sprite is 1 x 2
            # tiles in size, we add 1 to the 'y' position so the NPC's actual position will be on the bottom
            # portion of the sprite.
            npc.tile_pos = (float((npc.position[0] - self.global_x)) / float(
                self.tile_size[0]), (float((npc.position[1] - self.global_y)) / float(self.tile_size[1])) + 1)

            # Move the NPC with the map as it moves
            npc.position[0] -= self.global_x_diff
            npc.position[1] -= self.global_y_diff

            # if the npc has a path, move it along its path
            if npc.path:
                npc.move_by_path()

            npc.move(self.tile_size, self.time_passed_seconds, self)

        # Draw the bottom half of the player
        self.player1.draw(self.screen, "bottom")

        # Draw the medium level tiles. These tiles will appear above the player's body,
        # but below the player's head.
        for tile in self.medlayer_tiles:

            # Get the rectangle object of the tile that is going to be drawn so
            # we can see if it is going to be outside the visible screen area
            # or not
            if type(tile["surface"]) is pygame.Surface:
                tile_rect = pygame.Rect(tile["surface"].get_width(), tile["surface"].get_height(), tile[
                                        "position"][0] + self.global_x, tile["position"][1] + self.global_y)
            else:
                tile_rect = pygame.Rect(tile["surface"].getMaxSize()[0], tile["surface"].getMaxSize()[1],
                                        tile["position"][0] + self.global_x, tile["position"][1] + self.global_y)

            # If any part of the tile overlaps with the screen, then draw it to
            # the screen
            if self.screen_rect.colliderect(tile_rect):
                med_x = tile["position"][0] + self.orig_global_x
                med_y = tile["position"][1] + self.orig_global_y
                if type(tile["surface"]) is pygame.Surface:
                    self.screen.blit(tile["surface"], (med_x, med_y))
                else:
                    tile["surface"].blit(self.screen, (med_x, med_y))

        # Draw the top half of our NPCs above layer 4.
        for npc in self.npcs:
            npc.draw(self.screen, "top")

        # Draw the top half of the player above layer 4.
        self.player1.draw(self.screen, "top")

    def _collision_box_to_pgrect(self, collision_box):
        """Returns a pygame.Rect (in screen-coords) version of a collision box (in world-coords).
        """

        # For readability
        x = collision_box[0]
        y = collision_box[1]
        tile_width = self.tile_size[0]
        tile_height = self.tile_size[1]

        return pygame.Rect(x*tile_width + self.global_x,
                           y*tile_height + self.global_y,
                           tile_width,
                           tile_height)

    def _npc_to_pgrect(self, npc):
        """Returns a pygame.Rect (in screen-coords) of an NPC's bounding box.
        """

        return pygame.Rect(npc[0],
                           npc[1],
                           self.tile_size[0],
                           self.tile_size[1])

    def high_map_drawing(self, surface):
        """Draws map tiles above the players and NPCs
        """

        rect = surface.get_rect()

        # Draw the high level tiles
        for tile in self.highlayer_tiles:

            # Get the rectangle object of the tile that is going to be drawn so
            # we can see if it is going to be outside the visible screen area
            # or not
            if type(tile["surface"]) is pygame.Surface:
                tile_rect = pygame.Rect(tile["surface"].get_width(), tile["surface"].get_height(), tile[
                                        "position"][0] + self.global_x, tile["position"][1] + self.global_y)
            else:
                tile_rect = pygame.Rect(tile["surface"].getMaxSize()[0], tile["surface"].getMaxSize()[1],
                                        tile["position"][0] + self.global_x, tile["position"][1] + self.global_y)

            # If any part of the tile overlaps with the screen, then draw it
            if rect.colliderect(tile_rect):
                med_x = tile["position"][0] + self.orig_global_x
                med_y = tile["position"][1] + self.orig_global_y
                if type(tile["surface"]) is pygame.Surface:
                    surface.blit(tile["surface"], (med_x, med_y))
                else:
                    tile["surface"].blit(surface, (med_x, med_y))

        # Draw any map animations over everything.
        for animation_name, animation in self.game.animations.items():
            position = self.get_pos_from_tilepos(animation["position"])
            position = (position[0] + self.global_x_diff, position[1] + self.global_y_diff)
            animation["animation"].blit(surface, position)

        # If we want to draw the collision map for debug purposes
        if prepare.CONFIG.collision_map == "1":
            # We want to draw bright-red boxes over solid areas of the map.
            # First, let's get an iterator for the collision boxes.
            mapbox_iter = itertools.imap(self._collision_box_to_pgrect,
                                         self.collision_map)

            # Second, an iterator for NPC bounding boxes.
            npc_iter = itertools.imap(self._npc_to_pgrect,
                                      self.npcs)

            # Now draw them!
            solid_rects = itertools.chain(mapbox_iter, npc_iter)
            for item in solid_rects:
                surface.blit(self.collision_tile, (item[0], item[1]))

            if self.player1.direction["up"]:
                surface.blit(self.collision_tile, (
                    self.player1.position[0], self.player1.position[1] - self.tile_size[1]))
            elif self.player1.direction["down"]:
                surface.blit(self.collision_tile, (
                    self.player1.position[0], self.player1.position[1] + self.tile_size[1]))
            elif self.player1.direction["left"]:
                surface.blit(self.collision_tile, (
                    self.player1.position[0] - self.tile_size[0], self.player1.position[1]))
            elif self.player1.direction["right"]:
                surface.blit(self.collision_tile, (
                    self.player1.position[0] + self.tile_size[0], self.player1.position[1]))

    def midscreen_animations(self, surface):
        """Handles midscreen animations that will be drawn UNDER menus and dialog.

        :param surface: surface to draw on

        :rtype: None
        :returns: None

        """

        if self.cinema_state == "turning on":

            self.cinema_top['position'][
                1] += self.cinema_speed * self.time_passed_seconds
            self.cinema_bottom['position'][
                1] -= self.cinema_speed * self.time_passed_seconds

            # If we've reached our target position, stop the animation.
            if self.cinema_top['position'] >= self.cinema_top['on_position']:
                self.cinema_top['position'] = list(
                    self.cinema_top['on_position'])
                self.cinema_bottom['position'] = list(
                    self.cinema_bottom['on_position'])

                self.cinema_state = "on"

            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

        elif self.cinema_state == "on":
            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

        elif self.cinema_state == "turning off":

            self.cinema_top['position'][1] -= (
                self.cinema_speed * self.time_passed_seconds)
            self.cinema_bottom['position'][
                1] += self.cinema_speed * self.time_passed_seconds

            # If we've reached our target position, stop the animation.
            if self.cinema_top['position'][1] <= self.cinema_top['off_position'][1]:

                self.cinema_top['position'] = list(
                    self.cinema_top['off_position'])
                self.cinema_bottom['position'] = list(
                    self.cinema_bottom['off_position'])

                self.cinema_state = "off"

            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

    ####################################################
    #         Full Screen Animations Functions         #
    ####################################################
    def fullscreen_animations(self, surface):
        """Handles fullscreen animations such as transitions, cutscenes, etc.

        :param surface: Surface to draw onto

        :rtype: None
        :returns: None

        """

        # artificially set the time passed to make up for case
        # when map loads drop fps and causes the fade to be skipped
        td = 0.016  # 60 fps

        # FUCKIN' MATH! 0 = NO ALPHA NOT 255 DAMNIT BILLY!
        # if the value of start_transition event is set to true
        if self.start_transition:
            if self.transition_alpha == 0:
                self.SAVE_THIS_FUCKING_SCREEN = surface.copy()
            self.transition_surface = self.SAVE_THIS_FUCKING_SCREEN.copy()
            # fucking dumb ass math wont let me do less than 1 second so I had to speed that shit up so
            # I multiplied time_passed_seconds testing around making the fade faster because Billys'
            # teleport is TOO FUCKING FAST
            self.transition_alpha += 255 * (td / self.transition_time)
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                # created a black screen variable so it actually looks like he teleported, gotta figure out
                # how to make the event start earlier, initial testing proves I need sleep. Also billys'
                # teleport is STILL TOO FUCKING FAST!
                if self.black_screen >= 50:
                    self.black_screen = 50
                    self.start_transition_back = True
                    self.start_transition = False
                self.black_screen += 50 * (td / self.transition_time)
            self.transition_surface.set_alpha(self.transition_alpha)
            self.transition_surface.fill((0, 0, 0))
            surface.blit(self.transition_surface, (0, 0))
            # print(transition_alpha)

        # Perform a delayed teleport if we're also doing a teleport and we've
        # faded out completely
        if self.delayed_teleport and self.start_transition_back:
            self.global_x = self.delayed_x
            self.global_y = self.delayed_y

            if self.delayed_facing:
                self.player1.facing = self.delayed_facing
                self.delayed_facing = None

            # check if map has changed, and if so, change it
            map_name = prepare.BASEDIR + "resources/maps/" + self.delayed_mapname
            if map_name != self.current_map.filename:
                self.change_map(map_name)

            self.delayed_teleport = False

        # Replace this SAVE_THIS_FUCKING_SCREEN with the value of the blit of
        # the new map
        if self.start_transition_back:
            self.transition_back_surface = self.SAVE_THIS_FUCKING_SCREEN.copy()
            # same shit as above down here as well, except i slowed that shit
            # down
            self.transition_alpha -= 255 * (td / self.transition_time)
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.start_transition_back = False
                self.black_screen = 0
            self.transition_back_surface.set_alpha(self.transition_alpha)
            self.transition_back_surface.fill((0, 0, 0))
            surface.blit(self.transition_back_surface, (0, 0))
            self.game.event_data[
                "transition"] = False    # Set the transition variable in event_data to false when we're done

            # Update the server/clients of our new map and populate any other players.
            if self.game.isclient or self.game.ishost:
                self.game.add_clients_to_map(self.game.client.client.registry)
                self.game.client.update_player(self.player1.facing)

            # Update the location of the npcs. Doesn't send network data.
            for npc in self.npcs:
                char_dict = {"tile_pos": npc.tile_pos}
                networking.update_client(npc, char_dict, self.game)

            for npc in self.npcs_off_map:
                char_dict = {"tile_pos": npc.tile_pos}
                networking.update_client(npc, char_dict, self.game)

    ####################################################
    #             Map Change/Load Functions            #
    ####################################################
    def change_map(self, map_name):
        # Set the currently loaded map. This is needed because the event
        # engine loads event conditions and event actions from the currently
        # loaded map. If we change maps, we need to update this.

        # reset controls and stop moving to prevent player from
        # moving after the teleport and being out of control
        self.game.reset_controls()
        try:
            self.player1.direction['up'] = False
            self.player1.direction['down'] = False
            self.player1.direction['left'] = False
            self.player1.direction['right'] = False
            self.player1.moving = False
        except AttributeError:  # will be raised if this is first map change
            pass

        self.current_map = map.Map(map_name)
        self.event_engine.current_map = map.Map(map_name)

        self.tiles, self.collision_map, self.collision_lines_map, self.map_size = \
            self.current_map.loadfile(self.tile_size)

        # Get the events actions and conditions from the current map
        self.game.events = self.current_map.events

        # Clear out any existing NPCs
        self.npcs = []
        self.npcs_off_map = []

        # Scale the loaded tiles if enabled
        if prepare.CONFIG.scaling == "1":
            # Loop through each row in the map. Each row is a list of
            # Tile objects in that row.
            for y_pos, row in enumerate(self.tiles):
                # Now loop through each tile in the row and scale it accordingly.
                for x_pos, column in enumerate(row):
                    if column:
                        for layer_pos, tile in enumerate(column):
                            tile['surface'] = tools.scale_tile(tile['surface'], self.tile_size)
                            self.tiles[y_pos][x_pos][layer_pos] = tile

    def get_pos_from_tilepos(self, tile_position):
        """Returns the screen coordinate based on tile position.

        :param tile_position: An [x, y] tile position.

        :type event: List

        :rtype: List
        :returns: The pixel coordinates to draw at the given tile position.

        """
        x = (self.tile_size[0] * tile_position[0]) + self.global_x
        y = (self.tile_size[1] * tile_position[1]) + self.global_y

        return x, y


    def check_interactable_space(self):
        """Checks to see if any Npc objects around the player are interactable. It then populates a menu
        of possible actions.

        :param: None

        :rtype: Bool
        :returns: True if there is an Npc to interact with.

        """
        collision_dict = self.player1.get_collision_dict(self)
        player_tile_pos = ( int(round(self.player1.tile_pos[0])), int(round(self.player1.tile_pos[1])) )
        collisions = self.player1.collision_check(player_tile_pos, collision_dict, self.collision_lines_map)
        if not collisions:
            pass
        else:
            for direction in collisions:
                if self.player1.facing == direction:
                    if direction == "up":
                        tile = (player_tile_pos[0], player_tile_pos[1] - 1)
                    elif direction == "down":
                        tile = (player_tile_pos[0], player_tile_pos[1] + 1)
                    elif direction == "left":
                        tile = (player_tile_pos[0] - 1, player_tile_pos[1])
                    elif direction == "right":
                        tile = (player_tile_pos[0] + 1, player_tile_pos[1])
                    for npc in self.npcs:
                        tile_pos = ( int(round(npc.tile_pos[0])), int(round(npc.tile_pos[1])) )
                        if tile_pos == tile:
                            self.interaction_menu.visible = True
                            self.interaction_menu.interactable = True
                            self.interaction_menu.player = npc
                            self.interaction_menu.menu_items = ["Player Interactions:"]
                            for menu_item in npc.interactions:
                                self.interaction_menu.menu_items.append(menu_item)
                            return True
                        else: continue

    def handle_interaction(self, event_data, registry):
        """Presents options window when another player has interacted with this player.

        :param event_data: Information on the type of interaction and who sent it.
        :param registry:

        :type event_data: Dictionary
        :type registry: Dictionary

        :rtype: None
        :returns: None
        """
        print(event_data)
        target = registry[event_data["target"]]["sprite"]
        target_name = str(target.name)
        networking.update_client(target, event_data["char_dict"], self.game)
        if event_data["interaction"] == "DUEL":
            if not event_data["response"]:
                self.interaction_menu.visible = True
                self.interaction_menu.interactable = True
                self.interaction_menu.player = target
                self.interaction_menu.interaction = "DUEL"
                self.interaction_menu.menu_items = [target_name+" would like to Duel!","Accept","Decline"]
            else:
                if self.wants_duel:
                    if event_data["response"] == "Accept":
                        world = self.game.current_state
                        pd = world.player1.__dict__
                        event_data = {"type": "CLIENT_INTERACTION",
                                      "interaction": "START_DUEL",
                                      "target": [event_data["target"]],
                                      "response": None,
                                      "char_dict": {"monsters": pd["monsters"],
                                                    "inventory": pd["inventory"]
                                                    }

                                      }
                        self.game.server.notify_client_interaction(cuuid, event_data)

