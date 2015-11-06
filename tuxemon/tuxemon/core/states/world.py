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

# Import various python libraries
import logging
import pygame
import sys
import math
import os
import pprint

# Import Tuxemon internal libraries
from .. import tools, prepare
from ..components import screen
from ..components import config
from ..components import map
from ..components import pyganim
from ..components import player
from ..components import event
from ..components import save
from ..components import monster
from ..components import cli
from . import combat
from . import start

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

class World(tools._State):

    def __init__(self, game):
        # Initiate our common state properties.
        tools._State.__init__(self)

        # For some reason, importing menu only works here.
        from ..components import menu

        # Provide an instance of our scene manager to this scene.
        self.game = game

        # Provide access to the screen surface
        self.screen = game.screen
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
        self.scale = prepare.SCALE

        # Set the tiles and mapsize variables
        self.tiles = []
        self.map_size = []

        # Find out how many tiles can fit on the visible screen. We use this
        # so we draw only the tiles that are visible.
        self.visible_tiles = [
            int(math.ceil(self.resolution[0] / self.tile_size[0]) + 1),
            int(math.ceil(self.resolution[1] / self.tile_size[1]) + 1)]
        # self.visible_tiles = [5, 5]

        # Create a new map instance
        self.current_map = map.Map(prepare.BASEDIR + "resources/maps/%s" % prepare.CONFIG.starting_map)
        self.tiles, self.collision_map, self.collision_lines_map, self.map_size = \
            self.current_map.loadfile(self.tile_size)

        # Create an empty collision_rectmap list which contains rectangle
        # objects that we can test collision with
        self.collision_rectmap = []

        # Get the events actions and conditions from the current map
        self.game.events = self.current_map.events

        # Scale the loaded tiles if enabled
        if prepare.CONFIG.scaling == "1":
            x_pos = 0   # Here we need to keep track of the x index in list

            # Loop through each row in the map. Each row is a list of Tile
            # objects in that row.
            for row in self.tiles:
                # Here we need to keep track of the y index of the list within
                # the row
                y_pos = 0

                # Now loop through each tile in the row and scale it
                # accordingly.
                for column in row:
                    if column:
                        layer_pos = 0
                        for tile in column:
                            tile["surface"] = \
                                pygame.transform.scale(
                                    tile["surface"],
                                    (self.tile_size[0], self.tile_size[1]))
                            self.tiles[x_pos][y_pos][layer_pos] = tile
                            layer_pos += 1
                    y_pos += 1
                x_pos += 1

        # Set the world's current state. This is used for various functions.
        self.state = "World"


        ######################################################################
        #                           Player Details                           #
        ######################################################################

        self.player1 = prepare.player1
        self.npcs = []

        # Set the global coordinates used to pan the screen.
        self.start_position = prepare.CONFIG.starting_position
        self.global_x = self.player1.position[0] - \
            (self.start_position[0] * self.tile_size[0])
        self.global_y = self.player1.position[1] - \
            (self.start_position[1] * self.tile_size[1]) + self.tile_size[0]

        ######################################################################
        #                          Available Menus                           #
        ######################################################################

        # Dialog Window - Used to display dialog.
        DialogMenu = menu.dialog_menu.DialogMenu
        self.dialog_window = DialogMenu(self.screen,
                                        self.resolution,
                                        self,
                                        name="Dialog Window")

        # Main Menu - Allows users to open the main menu in game.
        MainMenu = menu.main_menu.MainMenu
        self.main_menu = MainMenu(self.screen,
                                  self.resolution,
                                  self,
                                  name="Main Menu")

        # Save Menu - Allows the user to save their game.
        SaveMenu = menu.save_menu.SaveMenu
        self.save_menu = SaveMenu(self.screen,
                                  self.resolution,
                                  self,
                                  name="Save Menu")

        # Enter Name Menu - Allows the user to input custom names. This is
        # used for naming the player as well as monsters.
        self.entername_menu = menu.Menu(self.screen,
                                        self.resolution,
                                        self,
                                        name="Enter Name Menu")

        # Display Name Menu - Displays the name entered in by the "Enter
        # Name" menu. This is considered a child of the Enter Name menu.
        self.displayname_menu = menu.Menu(self.screen,
                                          self.resolution,
                                          self,
                                          name="Display Entered Name")

        # This menu is just used to display a message that a particular
        # feature is not yet implemented.
        self.not_implmeneted_menu = menu.Menu(self.screen,
                                              self.resolution,
                                              self,
                                              name="Not implemented")

        # Item menus
        ItemMenu = menu.item_menu.ItemMenu
        self.item_menu = ItemMenu(self.screen,
                                  self.resolution,
                                  self)

        #Monster menu
        MonsterMenu = menu.monster_menu.MonsterMenu
        self.monster_menu = MonsterMenu(self.screen,
                                        self.resolution,
                                        self)

        # Add child menus to their parent menus
        self.entername_menu.add_child(self.displayname_menu)
        self.main_menu.add_child(self.save_menu)
        self.item_menu.add_child(self.monster_menu)

        # Set the window font sizes if they are not default
        self.entername_menu.font_size = 6

        # Set a variable to block regular player movement on the map when a
        # menu is active.
        self.menu_blocking = False

        # List of available menus
        self.menus = [self.dialog_window, self.main_menu, self.save_menu,
                      self.entername_menu, self.displayname_menu,
                      self.not_implmeneted_menu, self.item_menu, self.monster_menu]

        # Scale the menu borders of all menus
        for menu in self.menus:
            menu.scale = self.scale    # Set the scale of the menu.
            menu.set_font(size=menu.font_size * self.scale,
                          font=prepare.BASEDIR + "resources/font/PressStart2P.ttf",
                          color=(10, 10, 10),
                          spacing=menu.font_size * self.scale)

            # Scale the selection arrow image based on our game's scale.
            menu.arrow = pygame.transform.scale(
                menu.arrow,
                (menu.arrow.get_width() * self.scale,
                 menu.arrow.get_height() * self.scale))

            # Scale the border images based on our game's scale.
            for key, border in menu.border.items():
                menu.border[key] = pygame.transform.scale(
                    border,
                    (border.get_width() * self.scale,
                     border.get_height() * self.scale))

        # Set the size and position of all the windows.
        self.dialog_window.difference = \
            self.dialog_window.border["left-top"].get_width()
        self.dialog_window.size_x = \
            (self.resolution[0] / 2 - (self.dialog_window.difference))
        self.dialog_window.size_y = \
            (self.dialog_window.difference_y - self.dialog_window.difference)
        self.dialog_window.pos_x = \
            (self.resolution[0] / 2 - (self.dialog_window.size_x / 2))
        self.dialog_window.pos_y = \
            (self.dialog_window.difference_y * 3)
        self.dialog_window.visible = False
        self.dialog_window.interactable = False

        # The main menu will be positioned on the right-hand side of the
        # screen and be about 1/5th the width of the window.
        self.main_menu.size_x = int(self.resolution[0] / 5.)
        self.main_menu.size_y = self.resolution[1] - \
            (2 * self.main_menu.border["left-top"].get_width())
        self.main_menu.pos_x = ((self.resolution[0] / 6) * 5) - \
            self.main_menu.border["left-top"].get_width()
        self.main_menu.pos_y = 0 + self.main_menu.border["top"].get_height()
        self.main_menu.visible = False
        self.main_menu.interactable = False

        # The save menu will appear in the middle of the screen.
        self.save_menu.size_x = int(self.resolution[0] / 1.5)
        self.save_menu.size_y = int(self.resolution[1] / 1.5)
        self.save_menu.pos_x = (self.resolution[0] / 2) - \
            (self.save_menu.size_x / 2)
        self.save_menu.pos_y = (self.resolution[1] / 2) - \
            (self.save_menu.size_y / 2)
        self.save_menu.visible = False
        self.save_menu.interactable = False

        # The enter name menu will take up the full width of the screen
        # and fill up 3/4 of the height of the screen.
        self.entername_menu.size_x = self.resolution[0] - \
            (2 * self.entername_menu.border["left-top"].get_width())
        self.entername_menu.size_y = ((self.resolution[1] / 4) * 3) - \
            self.entername_menu.border["left-top"].get_width()
        self.entername_menu.pos_x = \
            self.dialog_window.border["left-top"].get_width()
        self.entername_menu.pos_y = self.resolution[1] / 4
        self.entername_menu.columns = 11   # The number of columns in each row
        self.entername_menu.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                                       'i', ' ', ' ', 'j', 'k', 'l', 'm', 'n',
                                       'o', 'p', 'q', 'r', ' ', ' ', 's', 't',
                                       'u', 'v', 'w', 'x', 'y', 'z', ' ', ' ',
                                       ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                       ' ', ' ', ' ', ' ', '0', '1', '2', '3',
                                       '4', '5', '6', '7', '8', '9', ' ',
                                       'CLR', 'END']
        self.entername_menu.visible = False
        self.entername_menu.interactable = False
        # self.entername_menu.visible = True  # for debug
        # self.entername_menu.interactable = True  # for debug
        # self.menu_blocking = True  # for debug

        self.displayname_menu.size_x = self.entername_menu.size_x
        self.displayname_menu.size_y = (self.entername_menu.size_y / 3) - (
            self.displayname_menu.border["left-top"].get_width() * 2)
        self.displayname_menu.pos_x = self.entername_menu.pos_x
        self.displayname_menu.pos_y = self.entername_menu.pos_x
        # self.displayname_menu.visible = True  # for debug
        self.displayname_menu.visible = False
        self.displayname_menu.interactable = False

        self.not_implmeneted_menu.size_x = int(prepare.SCREEN_SIZE[0] / 1.5)
        self.not_implmeneted_menu.size_y = prepare.SCREEN_SIZE[1] / 5
        self.not_implmeneted_menu.pos_x = (prepare.SCREEN_SIZE[0] / 2) - \
            (self.not_implmeneted_menu.size_x / 2)
        self.not_implmeneted_menu.pos_y = (prepare.SCREEN_SIZE[1] / 2) - \
            (self.not_implmeneted_menu.size_y / 2)
        self.not_implmeneted_menu.visible = False
        self.not_implmeneted_menu.interactable = False

        # Item Menu
        self.item_menu.size_x = prepare.SCREEN_SIZE[0]
        self.item_menu.size_y = prepare.SCREEN_SIZE[1]
        self.item_menu.pos_x = 0
        self.item_menu.pos_y = 0
        self.item_menu.visible = False
        self.item_menu.interactable = False

        # Monster Menu
        self.monster_menu.size_x = prepare.SCREEN_SIZE[0]
        self.monster_menu.size_y = prepare.SCREEN_SIZE[1]
        self.monster_menu.pos_x = 0
        self.monster_menu.pos_y = 0
        self.monster_menu.visible = False
        self.monster_menu.interactable = False

        # variables for transition
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

        # Variables used for battle transition animation. The battle
        # transition animation works by filling the screen with white at a
        # certain alpha level to create flashing.
        self.start_battle_transition = False    # Kick-off the transition.
        self.battle_transition_in_progress = False

        # Set the alpha level that the white screen will have.
        self.battle_transition_alpha = 0

        # Set the number of times the screen will flash before starting combat
        self.max_battle_flash_count = 6

        # Keep track of the current number of flashes that have passed
        self.battle_flash_count = 0

        # Either "up" or "down" indicating whether we are adding or
        # subtracting alpha levels.
        self.battle_flash_state = "up"

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
        #                          Event Engine                              #
        ######################################################################

        # Get a copy of the event engine from core.tools.Control.
        self.event_engine = self.game.event_engine

        # Set the currently loaded map. This is needed because the event
        # engine loads event conditions and event actions from the currently
        # loaded map. If we change maps, we need to update this.
        self.event_engine.current_map = self.current_map

        ######################################################################
        #                       Fullscreen Animations                        #
        ######################################################################

        # The cinema bars are used for cinematic moments.
        # The cinema state can be: "off", "on", "turning on" or "turning off"
        self.cinema_state = "off"
        self.cinema_speed = 15 * self.scale    # Pixels per second speed of the animation.

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


    def startup(self, current_time, persistant):
        """This is called every time the scene manager switches to this scene.

        :param current_time: Current time passed.
        :param persistant: Keep a dictionary of optional persistant variables.

        :type current_time: Integer
        :type persistant: Dictionary

        :rtype: None
        :returns: None


        **Examples:**

        >>> current_time
        2895
        >>> persistant
        {}

        """

        # Allow player movement and make all menus invisible.
        self.menu_blocking = False
        for menu in self.menus:
            menu.interactable = False
            menu.visible = False

        # Clear our next screen and any combat related variables.
        self.next = ""
        self.combat_started = False
        self.start_battle_transition = False
        self.battle_transition_in_progress = False


    def update(self, screen, keys, current_time, time_delta):
        """The primary game loop that executes the world's game functions every frame.

        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.
        :param time_delta: Amount of time passed since last frame.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer
        :type time_delta: Float

        :rtype: None
        :returns: None

        **Examples:**

        >>> surface
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """

        logger.debug("*** Game Loop Started ***")
        logger.debug(
            "Player Variables:" + str(self.player1.game_variables))

        # Tick our clock and limit the framerate to the fps specified in the
        # config
        self.time_passed_seconds = self.game.time_passed_seconds

        # Fill the screen background with black
        self.screen.fill((0, 0, 0))

        # Get all the pygame events
        self.events = keys

        # Get all the keys pressed
        self.pressed = pygame.key.get_pressed()
        self.pressed = list(self.pressed)
                            # Convert the keys pressed into a list so we can
                            # modify the values
        self.ctrl_held = self.pressed[
            pygame.K_LCTRL] or self.pressed[pygame.K_RCTRL]
        self.alt_held = self.pressed[
            pygame.K_LALT] or self.pressed[pygame.K_RALT]
        self.shift_held = self.pressed[
            pygame.K_LSHIFT] or self.pressed[pygame.K_RSHIFT]

        # Get the player's tile position based on the global_x/y variables. Since the player's sprite is 1 x 2
        # tiles in size, we add 1 to the 'y' position so the player's actual position will be on the bottom
        # portion of the sprite.
        self.player1.tile_pos = (float((self.player1.position[0] - self.global_x)) / float(
            self.tile_size[0]), (float((self.player1.position[1] - self.global_y)) / float(self.tile_size[1])) + 1)

        # Handle world events
        self.map_drawing()
        self.player_movement()
        self.high_map_drawing()
        self.midscreen_animations()
        self.draw_menus()
        self.fullscreen_animations()


    def get_event(self, event):
        """Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """

        # If the not implemented window is open, send pygame events to it.
        if self.not_implmeneted_menu.interactable:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.not_implmeneted_menu.visible = False
                self.not_implmeneted_menu.interactable = False

            # Don't process any other input until the user presses ENTER.
            return False

        # Handle events if the item menu is interactable.
        if self.item_menu.interactable:
            self.item_menu.get_event(event, self.game)

        # Handle events if the monster menu is interactable.
        if self.monster_menu.interactable:
            self.monster_menu.get_event(event, self.game)

        # If the dialog window is interactable/visible, send pygame events to it.
        if self.dialog_window.visible:
            self.dialog_window.get_event(event)

        # If the main menu is interactable, send pygame events to it.
        if self.main_menu.interactable:
            self.main_menu.get_event(event, self)

        # If the save menu is interactable, send pygame events to it.
        if self.save_menu.interactable:
            self.save_menu.get_event(event)

        # Exit the game if the close button is pressed
        if event.type == pygame.QUIT:
            self.exit = True
            self.game.exit = True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.main_menu.visible and self.main_menu.interactable:
                logger.info("Closing main menu!")
                self.main_menu.state = "closing"
                self.main_menu.interactable = False
                self.menu_blocking = False
            else:
                self.main_menu.visible = True
                self.menu_blocking = True
                self.player1.direction["up"] = False
                self.player1.direction["down"] = False
                self.player1.direction["left"] = False
                self.player1.direction["right"] = False

        # Only allow player movement if they are not in a menu and are not
        # in combat
        if not self.menu_blocking:
            # Handle Key DOWN events
            if event.type == pygame.KEYDOWN:
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

        # print self.events


    ####################################################
    #                   Map Drawing                    #
    ####################################################
    def map_drawing(self):
        """Draws the map tiles in a layered order.

        :param: None

        :rtype: None
        :returns: None

        """

        # Reset the higher layer tiles so we can draw them over the player
        self.highlayer_tiles = []
        self.medlayer_tiles = []

        starting_tile_x = - \
            (self.global_x / self.tile_size[0])
             # How many tiles over we have to draw the first tile
        starting_tile_y = - \
            (self.global_y / self.tile_size[
             1])  # How many tiles down we have to draw the first tile
        self.tile_buffer = 2  # This is how many tiles we should draw past the visible region

        # Loop through the number of visible tiles and draw only the tiles that
        # are visible
        for row in xrange(starting_tile_x - self.tile_buffer, starting_tile_x + self.visible_tiles[0]):
            if row > 0:

                for column in xrange(starting_tile_y - self.tile_buffer, starting_tile_y + self.visible_tiles[1]):
                    if row > 0:
                        try:
                            if self.tiles[row][column]:		# Check to see if a tile exists at this coordinates
                                for tile in self.tiles[row][column]:
                                    # Append the high level tiles to its own
                                    # list to be drawn over the player. Tiles on layer 4 will be drawn
                                    # above the player's body, but below the player's head.
                                    if tile["layer"] == 4:
                                        self.medlayer_tiles.append(tile)
                                    elif tile["layer"] > 4:
                                        self.highlayer_tiles.append(tile)
                                    else:
                                        self.screen.blit(tile["surface"],
                                                        (tile[
                                                            "position"][0] + self.global_x,
                                                         tile["position"][1] + self.global_y))

                        # If we try drawing a tile that is out of index range, that means we
                        # reached the end of the list, so just break the loop
                        except IndexError:
                            break

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

        # Handle tile based movement for the player
        if self.shift_held:
            self.player1.moverate = self.player1.runrate
        else:
            self.player1.moverate = self.player1.walkrate

        # Check to see if the player is colliding with anything
        self.collision_rectmap = []
        for item in self.collision_map:
            self.collision_rectmap.append(
                pygame.Rect(
                    (item[0] * self.tile_size[0]) + self.global_x,
                    (item[1] * self.tile_size[0]) + self.global_y, self.tile_size[0], self.tile_size[1]))

        # Add any NPC's to the collision rectangle map. We use this to see if
        # the player is colliding or not
        for npc in self.npcs:
            self.collision_rectmap.append(
                pygame.Rect(npc.position[0], npc.position[1], self.tile_size[0], self.tile_size[1]))

        # Set the global_x/y when the player moves around
        self.global_x, self.global_y = self.player1.move(
            self.screen, self.tile_size, self.time_passed_seconds, (self.global_x, self.global_y), self)

        # Find out how many pixels we've moved since we started moving
        self.global_x_diff = self.orig_global_x - self.global_x
        self.global_y_diff = self.orig_global_y - self.global_y

        # Draw any game NPC's
        for npc in self.npcs:
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
            #print "npc.tile_pos="+str(npc.tile_pos)

            # if the npc has a path, move it along its path
            if npc.path:
                npc.move_by_path()

            npc.move(self.tile_size, self.time_passed_seconds, self)

            # Reset our directions after moving.
            npc.direction["up"] = False
            npc.direction["down"] = False
            npc.direction["left"] = False
            npc.direction["right"] = False

            # Draw the bottom part of the NPC.
            npc.draw(self.screen, "bottom")

        # Draw the bottom half of the player
        self.player1.draw(self.screen, "bottom")

        # Draw the medium level tiles. These tiles will appear above the player's body,
        # but below the player's head.
        for tile in self.medlayer_tiles:

            # Get the rectangle object of the tile that is going to be drawn so
            # we can see if it is going to be outside the visible screen area
            # or not
            tile_rect = pygame.Rect(tile["surface"].get_width(), tile["surface"].get_height(), tile[
                                    "position"][0] + self.global_x, tile["position"][1] + self.global_y)

            # If any part of the tile overlaps with the screen, then draw it to
            # the screen
            if self.screen_rect.colliderect(tile_rect):
                self.screen.blit(
                    tile["surface"], (tile["position"][0] + self.orig_global_x, tile["position"][1] + self.orig_global_y))

        # Draw the top half of our NPCs above layer 4.
        for npc in self.npcs:
            npc.draw(self.screen, "top")

        # Draw the top half of the player above layer 4.
        self.player1.draw(self.screen, "top")


    def high_map_drawing(self):
        """Draws map tiles above the players and NPCs
        """

        # Draw the high level tiles
        for tile in self.highlayer_tiles:

            # Get the rectangle object of the tile that is going to be drawn so
            # we can see if it is going to be outside the visible screen area
            # or not
            tile_rect = pygame.Rect(tile["surface"].get_width(), tile["surface"].get_height(), tile[
                                    "position"][0] + self.global_x, tile["position"][1] + self.global_y)

            # If any part of the tile overlaps with the screen, then draw it to
            # the screen
            if self.screen_rect.colliderect(tile_rect):
                self.screen.blit(
                    tile["surface"], (tile["position"][0] + self.orig_global_x, tile["position"][1] + self.orig_global_y))

        # Draw any map animations over everything.
        for animation_name, animation in self.game.animations.items():
            position = self.get_pos_from_tilepos(animation["position"])
            position = (position[0] + self.global_x_diff, position[1] + self.global_y_diff)
            animation["animation"].blit(self.screen, position)

        # If we want to draw the collision map for debug purposes
        if prepare.CONFIG.collision_map == "1":
            for item in self.collision_rectmap:
                self.screen.blit(self.collision_tile, (item[0], item[1]))

            if self.player1.direction["up"]:
                self.screen.blit(self.collision_tile, (
                    self.player1.position[0], self.player1.position[1] - self.tile_size[1]))
            elif self.player1.direction["down"]:
                self.screen.blit(self.collision_tile, (
                    self.player1.position[0], self.player1.position[1] + self.tile_size[1]))
            elif self.player1.direction["left"]:
                self.screen.blit(self.collision_tile, (
                    self.player1.position[0] - self.tile_size[0], self.player1.position[1]))
            elif self.player1.direction["right"]:
                self.screen.blit(self.collision_tile, (
                    self.player1.position[0] + self.tile_size[0], self.player1.position[1]))

    ####################################################
    #                 Menu Functions                   #
    ####################################################
    def draw_menus(self):
        """Handles the drawing of menus.

        :param: None

        :rtype: None
        :returns: None

        """

        # Enter Name Menu
        if self.entername_menu.visible:

            self.entername_menu.draw()
            self.entername_menu.draw_textItem(
                self.entername_menu.letters, self.entername_menu.columns)

            if self.entername_menu.interactable:
                self.entername_menu.update_menu_selection(
                    self.events, self, input_allowed=True)

        # Display Name Menu
        if self.displayname_menu.visible:

            self.displayname_menu.draw()
            self.displayname_menu.draw_text(
                'Enter Name:\\n\\n', pos_y=2 * self.scale)

            if len(self.entername_menu.input) > 0:
                self.displayname_menu.draw_text(
                    self.entername_menu.input, align="middle", justify="center", font_size=7)

        # Dialog Window
        # Only draw the dialog menu if it hasn't been opened within 0.5 seconds. This prevents
        # the dialog menu from opening up again immediately when the user dismisses the menu.
        if (self.dialog_window.visible) and (self.dialog_window.elapsed_time >= self.dialog_window.delay):
            self.dialog_window.draw()
            self.dialog_window.draw_text()
        else:
            # Keep track how long it's been since the dialog menu has been last opened.
            self.dialog_window.visible = False
            if self.dialog_window.elapsed_time < self.dialog_window.delay:
                self.dialog_window.elapsed_time += self.time_passed_seconds

        # Main Menu
        if self.main_menu.visible:
            # Take a copy of the screen before we open the menu so we can save
            # it as a screenshot with no menus
            self.save_screenshot = self.screen.copy()

            # Set up menu animations
            animation_speed = self.resolution[0] / 1.1
            if self.main_menu.state == "closed":
                self.main_menu.pos_x = self.resolution[0] + \
                    self.main_menu.border['left'].get_width()
                self.main_menu.state = "opening"

            elif self.main_menu.state == "opening":
                self.main_menu.pos_x -= animation_speed * \
                    self.time_passed_seconds

                if self.main_menu.pos_x <= self.resolution[0] - self.main_menu.size_x - self.main_menu.border['left'].get_width():
                    self.main_menu.pos_x = self.resolution[
                        0] - self.main_menu.size_x - self.main_menu.border['left'].get_width()
                    self.main_menu.state = "open"

            elif self.main_menu.state == "closing":
                self.main_menu.pos_x += animation_speed * \
                    self.time_passed_seconds

                if self.main_menu.pos_x >= self.resolution[0] + self.main_menu.border['left'].get_width():
                    self.main_menu.pos_x = self.resolution[
                        0] + self.main_menu.border['left'].get_width()
                    self.main_menu.state = "closed"
                    self.main_menu.visible = False
                    self.main_menu.interactable = False

            self.main_menu.draw()
            self.main_menu.draw_textItem(
                ["JOURNAL", "TUXEMON", "BAG", "PLAYER", "SAVE", "LOAD", "OPTIONS", "EXIT"], 1)

            if self.main_menu.save:
                self.save_menu.visible = True
                self.main_menu.interactable = False
                # core.save.save(screen, player1, 1, current_map)
                # main_menu.save = False
            else:
                if self.main_menu.state == "open" or self.main_menu.state == "opening":
                    self.main_menu.interactable = True

        # Save Menu
        if self.save_menu.visible:
            # Set the save game variables so we can save the game in the menu
            # class
            self.save_menu.save_data = {
                'screen': self.save_screenshot,
                'player': self.player1,
                'current_map': self.current_map}

            # draw the menu and handle key events
            self.save_menu.draw()

            # If we closed the save menu, set the main menu's save variable to
            # false
            if not self.save_menu.visible:
                self.main_menu.save = False

        # Draw the Item Menu
        if self.item_menu.visible:
            self.item_menu.draw(draw_borders=False)

        # Draw the Monster menu
        if self.monster_menu.visible:
            self.monster_menu.draw(draw_borders=False)

        # Not implemented menu
        if self.not_implmeneted_menu.visible:
            self.not_implmeneted_menu.draw()
            self.not_implmeneted_menu.draw_text("This feature is not yet implemented.",
                justify="center", align="middle")


    def midscreen_animations(self):
        """Handles midscreen animations that will be drawn UNDER menus and dialog.

        :param: None

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
            self.screen.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            self.screen.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

        elif self.cinema_state == "on":
            # Draw the cinema bars
            self.screen.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            self.screen.blit(
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
            self.screen.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            self.screen.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

    ####################################################
    #         Full Screen Animations Functions         #
    ####################################################
    def fullscreen_animations(self):
        """Handles fullscreen animations such as transitions, cutscenes, etc.

        :param: None

        :rtype: None
        :returns: None

        """

        if self.start_battle_transition:
            logger.info("Initializing battle transition")
            self.game.rumble.rumble(-1, length=1.5)
            self.battle_transition_in_progress = True
            self.transition_surface = pygame.Surface(self.resolution)
            self.transition_surface.fill((255, 255, 255))
            self.start_battle_transition = False

            # Stop player map movement
            self.menu_blocking = True

        if self.battle_transition_in_progress:
            logger.info("Battle transition!")

            flash_time = 0.2  # Time in seconds between flashes

            # self.battle_transition_alpha
            if self.battle_flash_state == "up":
                self.battle_transition_alpha += (
                    255 * ((self.time_passed_seconds) / flash_time))

            elif self.battle_flash_state == "down":
                self.battle_transition_alpha -= (
                    255 * ((self.time_passed_seconds) / flash_time))

            if self.battle_transition_alpha >= 255:
                self.battle_flash_state = "down"
                self.battle_flash_count += 1
            elif self.battle_transition_alpha <= 0:
                self.battle_flash_state = "up"
                self.battle_flash_count += 1

            # If we've hit our max number of flashes, stop the battle
            # transition animation.
            if self.battle_flash_count > self.max_battle_flash_count:
                logger.info("Flashed " + str(self.battle_flash_count) +
                    " times. Stopping transition.")
                self.battle_transition_in_progress = False
                self.battle_flash_count = 0

                # Set our next scene to be "COMBAT". Then, setting "self.done" to True
                # will cause the scene manager to load the next scene.
                self.next = "COMBAT"
                self.done = True

            # Set the alpha of the screen and fill the screen with white at
            # that alpha level.
            self.transition_surface.set_alpha(self.battle_transition_alpha)
            self.screen.blit(self.transition_surface, (0, 0))

        # FUCKIN' MATH! 0 = NO ALPHA NOT 255 DAMNIT BILLY!
        # if the value of start_transition event is set to true
        if self.start_transition:
            if self.transition_alpha == 0:
                self.SAVE_THIS_FUCKING_SCREEN = self.screen.copy()
            self.transition_surface = self.SAVE_THIS_FUCKING_SCREEN.copy()
            # fucking dumb ass math wont let me do less than 1 second so I had to speed that shit up so
            # I multiplied time_passed_seconds testing around making the fade faster because Billys'
            # teleport is TOO FUCKING FAST
            self.transition_alpha += (
                255 * ((self.time_passed_seconds) / self.transition_time))
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                # created a black screen variable so it actually looks like he teleported, gotta figure out
                # how to make the event start earlier, initial testing proves I need sleep. Also billys'
                # teleport is STILL TOO FUCKING FAST!
                if self.black_screen >= 50:
                    self.black_screen = 50
                    self.start_transition_back = True
                    self.start_transition = False
                self.black_screen += (
                    50 * ((self.time_passed_seconds) / self.transition_time))
            self.transition_surface.set_alpha(self.transition_alpha)
            self.transition_surface.fill((0, 0, 0))
            self.screen.blit(self.transition_surface, (0, 0))
            # print transition_alpha

        # Perform a delayed teleport if we're also doing a teleport and we've
        # faded out completely
        if self.delayed_teleport and self.start_transition_back:
            self.global_x = self.delayed_x
            self.global_y = self.delayed_y

            if self.delayed_facing:
                self.player1.facing = self.delayed_facing
                self.delayed_facing = None

            if prepare.BASEDIR + "resources/maps/" + self.delayed_mapname != self.current_map.filename:
                self.current_map = map.Map(
                    prepare.BASEDIR + "resources/maps/" + self.delayed_mapname)
                self.event_engine.current_map = map.Map(
                    prepare.BASEDIR + "resources/maps/" + self.delayed_mapname)
                self.tiles, self.collision_map, self.collision_lines_map, self.map_size = self.current_map.loadfile(
                    self.tile_size)
                self.game.events = self.current_map.events

                # Clear out any existing NPCs
                self.npcs = []

                # Scale the loaded tiles if enabled
                if prepare.CONFIG.scaling == "1":
                    x_pos = 0        # Here we need to keep track of the x index of the list
                    # Loop through each row in the map. Each row is a list of
                    # Tile objects in that row.
                    for row in self.tiles:
                        y_pos = 0       # Here we need to keep track of the y index of the list within the row
                        # Now loop through each tile in the row and scale it
                        # accordingly.
                        for column in row:
                            if column:
                                layer_pos = 0
                                for tile in column:
                                    tile["surface"] = pygame.transform.scale(
                                        tile["surface"], (self.tile_size[0], self.tile_size[1]))
                                    self.tiles[x_pos][y_pos][layer_pos] = tile
                                    layer_pos += 1
                            y_pos += 1
                        x_pos += 1

            self.delayed_teleport = False

        # Replace this SAVE_THIS_FUCKING_SCREEN with the value of the blit of
        # the new map
        if self.start_transition_back:
            self.transition_back_surface = self.SAVE_THIS_FUCKING_SCREEN.copy()
            # same shit as above down here as well, except i slowed that shit
            # down
            self.transition_alpha -= (
                255 * ((self.time_passed_seconds) / self.transition_time))
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.start_transition_back = False
                self.black_screen = 0
            self.transition_back_surface.set_alpha(self.transition_alpha)
            self.transition_back_surface.fill((0, 0, 0))
            self.screen.blit(self.transition_back_surface, (0, 0))
            # print transition_alpha
            self.game.event_data[
                "transition"] = False    # Set the transition variable in event_data to false when we're done


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
