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
# core.components.menu Menu handling module.
#
#

import logging
import pygame
import math
import os
import sys

from core.components.ui import UserInterface
from .. import eztext
from .. import plugin
from ... import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.menu successfully imported")

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


class Menu(UserInterface):
    """A class to create menu objects.

    :param screen: The pygame.display surface to draw the menu to.
    :param resolution: A tuple of the display's resolution in (x, y) format. TODO: We should be
        able to get this from pygame.display
    :param name: A human readable name of the menu. Used for debugging purposes.
        *Default: "Menu"*
    :param background: String of the path to a background image to use for the menu.
        *Default: None*
    :param scale_borders: True or false value indicating whether or not to scale the border images
        to match the current resolution when creating the menu. If this is not done, then your
        borders will only be 2 pixels large, regardless of the resolution the game.
        *Default: False*

    :type screen: pygame.display
    :type resolution: Tuple
    :type name: String
    :type background: String
    :type scale_borders: Boolean

    :ivar size_x: The width of the menu in pixels, defaults to 400.
    :ivar size_y: The height of the menu in pixels, defaults to 200.
    :ivar pos_x: The x position of the top-left corner of the menu, defaults to the center of the
        screen.
    :ivar pos_y: The y position of the top-left corner of the mnu, defaults to the center of the
        screen.
    :ivar color: The (r, g, b) color value of the window's background color, defaults to (248, 248,
        248).
    :ivar state: An arbitrary state of the menu. E.g. "opening" or "closing".
    :ivar visible: Whether or not the menu is visible, defaults to False.
    :ivar selected_menu_item: The index position of the currently selected menu item.
    :ivar menu_items: A list of available menu items.

    To create a new menu, simply create a new menu instance and then set the size and coordinates
    of the menu like this:

    Example:

    >>> menu = Menu(screen, resolution)
    >>> menu.size_x = 200
    >>> menu.size_y = 100
    >>> menu.pos_x = 500
    >>> menu.pos_y = 500
    >>> menu.draw()

    """

    def __init__(self, screen, resolution, game, name="Menu", background=None, scale_borders=False):

        self.name = name                                    # An arbitrary name of the menu
        self.game = game
        self.previous_menu = None

        self.size_x = 400                                   # The width of the menu in pixels
        self.size_y = 200                                   # The height of the menu in pixels
        self.pos_x = (resolution[0] / 2) - (self.size_x/2)  # The x position of the top-left corner of the menu
        self.pos_y = (resolution[1] / 2) - (self.size_y/2)  # The y position of the top-left corner of the menu
        self.resolution_x = resolution[0]                   # The screen's current x resolution
        self.resolution_y = resolution[1]                   # The screen's current y resolution
        self.color = (248, 248, 248)                        # The window's background color
        self.screen = screen                                # A pygame screen object to draw the menu to
        self.state = ""
        self.timer = 0
        self.visible = False
        self.menuitempositions = False
        self.text = " "
        self.selected_menu_item = 0	# This is used to see what menu item is selected
        self.selected_row = 1       # The currently selected row (starts at 1 instead of 0)
        self.menu_items = []
        self.menu_icons = []
        self.scale = 1
        self.interactable = True
        self.columns = 1

        # These variables are used to pop up a dialog for a specific period of time.
        self.delay = 4.0                     # This is used to optionally show this window for this many seconds before closing
        self.elapsed_time = self.delay       # Keep track of how long in seconds it has been since we've opened this menu.

        # These variables are used to establish child-parent relationships between menus
        self.parents = []
        self.children = []

        # User input string. Used for the name-entering system
        self.input = ""             # User input string. Used to store a string inputted by the user.
        self.input_max_size = 8     # The maximum number of characters the user can input.

        # Adding static variables for menus for the bottom 1/2 of the screen (mainly for states.combat)
        self.difference_x = ((resolution[0]/4)*3)
        self.difference_y = ((resolution[1]/4))

        # Native resolution is similar to the old gameboy resolution. This is used for scaling.
        self.native_resolution = [240, 160]


        # Font shit for drawing text
        self.font_size = 4
        self.min_font_size = 7
        self.font = pygame.font.Font(prepare.BASEDIR + "resources/font/PressStart2P.ttf", self.font_size)
        self.font_color = (10, 10, 10)
        self.line_spacing = 10

        self.border = {
           'left':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-left.png").convert_alpha(),
           'right':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-right.png").convert_alpha(),
           'top':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-top.png").convert_alpha(),
           'bottom':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-bottom.png").convert_alpha(),
           'left-top':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-left-top.png").convert_alpha(),
           'left-bottom':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-left-bottom.png").convert_alpha(),
           'right-top':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-right-top.png").convert_alpha(),
           'right-bottom':pygame.image.load(prepare.BASEDIR + "resources/gfx/menu-right-bottom.png").convert_alpha(),
           }

        # Scale the window's borders based on the game's scale.
        if scale_borders:
            self.border = self.scale_borders(self.border)

        self.arrow = pygame.image.load(prepare.BASEDIR + "resources/gfx/arrow.png").convert_alpha()

        self.difference = self.border["left-top"].get_width()  # TODO: Rename to "border_size"
        self.border_size = self.border["left-top"].get_width()

        # Set the background image of this menu if one was specified.
        if background:
            self.background = pygame.image.load(background).convert_alpha()
        else:
            self.background = None


    def __setattr__(self, key, value):
        """Detects changes to the menu class' attributes.

        :param key: The attribute being changed.
        :param value: The value the attribute is being changed to.

        :type key: String
        :type value: Any

        """
        #print("Changing", key, "to", value)

        # If the background surface changes, scale it to the size of the window.
        if key == "background":
            if value:
                value = pygame.transform.scale(value, (self.size_x, self.size_y))

        # If the size of our menu changes, scale the border images so they are the same size as
        # the menu itself.
        elif key == "size_x":
            if "border" in self.__dict__:
                self.__dict__[key] = value
                self.scale_sides()
                return

        elif key == "size_y":
            if "border" in self.__dict__:
                self.__dict__[key] = value
                self.scale_sides()
                return

        elif key == "border":
            if "background" in self.__dict__:
                self.__dict__[key] = value
                self.difference = self.border["left-top"].get_width()
                self.scale_sides()
                return

        self.__dict__[key] = value


    def scale_borders(self, borders):
        """Scales the menu's border images based on the game's scale. This should be called
        ONCE to ensure that the menu images are the correct size based on the game's
        resolution. This method differs from the "scale_sides" method as that scales the
        menu images to fit the size of the menu itself.

        :param borders: A dictionary containing pygame surfaces of all sides of the menu
            borders.

        :type borders: Dictionary

        :rtype: Dictionary
        :returns: A modified dictionary of scaled border images

        **Examples:**

        >>> main_menu = Menu(screen, resolution)
        >>> borders = {
        ...   'left':pygame.image.load("resources/gfx/menu-left.png").convert_alpha(),
        ...   'right':pygame.image.load("resources/gfx/menu-right.png").convert_alpha(),
        ...   'top':pygame.image.load("resources/gfx/menu-top.png").convert_alpha(),
        ...   'bottom':pygame.image.load("resources/gfx/menu-bottom.png").convert_alpha(),
        ...   'left-top':pygame.image.load("resources/gfx/menu-left-top.png").convert_alpha(),
        ...   'left-bottom':pygame.image.load("resources/gfx/menu-left-bottom.png").convert_alpha(),
        ...   'right-top':pygame.image.load("resources/gfx/menu-right-top.png").convert_alpha(),
        ...   'right-bottom':pygame.image.load("resources/gfx/menu-right-bottom.png").convert_alpha(),
        ...   }
        >>> main_menu.scale_borders(borders)

        """

        scaled_borders = {}

        # Scale the window's borders based on the game's scale.
        for key, border in borders.items():
            scaled_borders[key] = pygame.transform.scale(
                border,
                (border.get_width() * prepare.SCALE, border.get_height() * prepare.SCALE))

        self.border_size = scaled_borders["left-top"].get_width()
        return scaled_borders


    def add_child(self, menu):
        """Add a menu object as a child of this menu. This is used to establish a parent-child
        relationship between menus.

        :param menu: A core.components.menu.Menu object that will be the child of this menu.

        :type menu: core.components.menu.Menu

        :rtype: None
        :returns: None

        **Examples:**

        >>> main_menu = Menu(screen, resolution)
        >>> sub_menu = SaveMenu(screen, resolution)
        ...
        >>> main_menu.add_child(sub_menu)
        ...
        >>> main_menu.children
        ... [<core.components.menu.SaveMenu instance at 0x2002c68>]
        >>> sub_menu.parents
        ... [<core.components.menu.Menu instance at 0x2002320>]

        """

        self.children.append(menu)
        menu.parents.append(self)


    def remove_child(self, menu):
        """Removes a child from this menu object. This is used to destroy a parent-child
        relationship between menus.

        :param menu: A core.components.menu.Menu object to remove.

        :type menu: core.components.menu.Menu

        :rtype: None
        :returns: None

        **Examples:**

        >>> main_menu = Menu(screen, resolution)
        >>> sub_menu = SaveMenu(screen, resolution)
        ...
        >>> main_menu.add_child(sub_menu)
        ...
        >>> main_menu.children
        ... [<core.components.menu.SaveMenu instance at 0x2002c68>]
        >>> sub_menu.parents
        ... [<core.components.menu.Menu instance at 0x2002320>]
        ...
        >>> main_menu.remove_child(sub_menu)
        ...
        >>> main_menu.children
        ... []
        >>> sub_menu.parents
        ... []

        """

        # If the menu exists as a child of this menu, remove it
        if menu in self.children:
            self.children.remove(menu)

        # If the menu does not exist as a child menu, log an error and return nothing
        else:
            logger.WARNING("Child does not exist")
            return None

        # If the menu was a child of this menu, remove it as a parent from the child menu
        menu.parents.remove(self)


    def draw(self, draw_borders=True, fill_background=True):
        """Draws the menu object to a pygame screen.

        :param draw_borders: True or False value of whether or not to draw the borders
        :param fill_background: True or False value of whether or not to fill the menu background
            with the menu color. If a menu background was set, it will scale the background image
            to fit the size of the menu.

        :type draw_borders: boolean
        :type fill_background: boolean

        :rtype: None
        :returns: None

        """

        # Draw the background box
        if fill_background:
            # If a background image was specified, draw that. Otherwise, fill it in with the menu
            # color.
            if self.background:
                self.screen.blit(self.background, (self.pos_x, self.pos_y))
            else:
                pygame.draw.rect(self.screen, self.color,
                                 (self.pos_x, self.pos_y, self.size_x, self.size_y))

        # Draw the border images.
        if draw_borders:
            self.screen.blit(self.border["right"],
                             (self.pos_x + self.size_x, self.pos_y) )
            self.screen.blit(self.border["left"],
                             (self.pos_x - self.border["left"].get_width(), self.pos_y) )
            self.screen.blit(self.border["top"],
                             (self.pos_x, self.pos_y - self.border["top"].get_height()) )
            self.screen.blit(self.border["bottom"],
                             (self.pos_x, self.pos_y + self.size_y) )

            # Draw the corners
            self.screen.blit(self.border["left-top"],
                (self.pos_x - self.border["left-top"].get_width(),
                 self.pos_y - self.border["left-top"].get_height()))
            self.screen.blit(self.border["left-bottom"],
                (self.pos_x - self.border["left-bottom"].get_width(),
                 self.pos_y + self.size_y))

            self.screen.blit(self.border["right-top"],
                (self.pos_x + self.size_x,
                 self.pos_y - self.border["left-top"].get_height()))
            self.screen.blit(self.border["right-bottom"],
                (self.pos_x + self.size_x,
                 self.pos_y + self.size_y ))


    def draw_text(self, text=None, pos_x=None, pos_y=None, justify="left", align=None, font_size=None, font_color=None):
        """Draws text to the current menu object. If the text exceeds the window size, it will
        autowrap. To place text on a new line, put TWO newline characters (\\n)  in your text.

        :param text: The text that you want to draw to the current menu item.
            *Default: core.components.menu.Menu.text*
        :param pos_x: The horizontal pixel position of the text relative to the menu's position.
            *Default: 0*
        :param pos_y: The vertical pixel position of the text relative to the menu's position.
            *Default: 0*
        :param justify: Left, center, or right justify the text. Valid options: "left", "center",
            "right". *Default: "left"*
        :param align: Align the text to the top, middle, or bottom of the menu. Valid options:
            "top", "middle", "bottom". *Default: "top"*
        :param font_size: Size of the font in pixels BEFORE scaling is done. *Default: 4*
        :param font_color: Tuple of RGB values of the font color to use. *Default: (10, 10, 10)*

        :type text: String
        :type pos_x: Integer
        :type pos_y: Integer
        :type justify: String
        :type align: String
        :type font_size: Integer
        :type font_color: Tuple

        :rtype: None
        :returns: None

        **Examples:**

        >>> menu.draw_text("boo", justify="center", align="middle")

        .. image:: images/menu/justify_center.png

        """

        # If the position isn't specified in the function, set it to the current intance's
        # position. Otherwise, set it to the relative position
        if (pos_x == None):
            pos_x = self.pos_x
        else:
            pos_x = pos_x + self.pos_x
        if (pos_y == None):
            pos_y = self.pos_y
        else:
            pos_y = pos_y + self.pos_y
        if text == None:
            text = self.text

        # Set up our font that we're going to use, including size, color, etc.
        font = self.font

        # If font_size was specified, we need to create a new font object
        if font_size:
            font_size *= self.scale    # Scale the font if graphic scaling is enabled
            if font_size < self.min_font_size:
                font_size = self.min_font_size
            font = pygame.font.Font(prepare.BASEDIR + "resources/font/PressStart2P.ttf", font_size)

        # If a font color wasn't specified, use the menu's font color
        if not font_color:
            font_color = self.font_color


        # Create a text surface so we can determine how many pixels
        # wide each character is
        text_surface = font.render(text, 1, font_color)

        # Calculate the number of pixels per letter based on the size
        # of the text and the number of characters in the text
        pixels_per_letter = text_surface.get_width() / len(text)

        # Create a list of the lines of text as well as a list of the
        # individual words so we can check each line's length in pixels
        lines = []
        wordlist = []

        # Loop through each word in the text and add it to the word list
        for word in text.split():

            # If there is a linebreak in this word, then split it up into a list separated by \n
            if "\\n" in word:
                w = word.split("\\n")

                # Loop through the list and every time we encounter a blank string, then that is
                # a new line. So we append the current line and reset the word list for a new line
                for item in w:
                    if item == '':
                        # This is a new line!
                        lines.append(" ".join(wordlist))
                        wordlist = []
                    # If we encounter an actual word, then just append it to the word list
                    else:
                        wordlist.append(item)

            # If there's no line break, continue normally to word wrap
            else:

                # Append the word to the current line
                wordlist.append(word)

                # Here, we convert the list into a string separated by spaces and multiply
                # the number of characters in the string by the number of pixels per letter
                # that we calculated earlier. This will let us know how large the text will
                # be in pixels.
                if len(" ".join(wordlist)) * pixels_per_letter > self.size_x:
                    # If the size exceeds the width of the menu, then append the line to the
                    # list of lines, but stripping off the last word we added (because this
                    # was the word that made us exceed the menubox's size.
                    lines.append(" ".join(wordlist[:-1]))

                    # Reset the wordlist for the next line and add the word we stripped off
                    wordlist = []
                    wordlist.append(word)


        # If the last line is not blank, then append it to the list
        if " ".join(wordlist) != '':
            lines.append(" ".join(wordlist))



        # If the justification was set, handle the position of the text automatically
        if justify == "center":
            if len(lines) > 0:
                pos_x = (self.pos_x + (self.size_x / 2)) - \
                    ((len(lines[0]) * pixels_per_letter) / 2)
            else:
                pos_x = 0

        elif justify == "right":
             raise NotImplementedError("Needs to be implemented")

        # If text alignment was set, handle the position of the text automatically
        if align == "middle":
            pos_y = (self.pos_y + (self.size_y / 2)) - \
                ((text_surface.get_height() * len(lines)) / 2)

        elif align == "bottom":
            raise NotImplementedError("Needs to be implemented")


        # Set a spacing variable that we will add to to space each line.
        spacing = 0
        for item in lines:
            line = font.render(item, 1, self.font_color)

            self.screen.blit(line, (pos_x, pos_y + spacing))
            spacing += line.get_height() + self.line_spacing


    def update_menu_selection(self, event, game=None, input_allowed=False):
        """Handles player input events for text menu items when this menu is interactable. This
        includes moving your menu selection around a grid of selectable text items. This is most
        notably used in the name entering system.

        :param events: A pygame event from pygame.event.get()
        :param game: An optional instance of the game itself so we can directly manipulate its
            variables. *Default: None*
        :param input_allowed: True or False value to allow the player to use the menu to input
            text. *Default: False*

        :type events: pygame.event
        :type game: core.control.Control
        :type input_allowed: Boolean

        :rtype: None
        :returns: None


        This example shows you how you can draw a menu with several columns and rows of selectable
        menu items.

        >>> entername_menu = core.components.menu.Menu(screen, resolution)
        >>> entername_menu.columns = 11   # The number of columns in each row
        >>> entername_menu.letters = ['a','b','c','d','e','f','g','h','i',' ',' ','j','k','l','m','n','o','p','q','r',' ',' ','s','t','u','v','w','x','y','z',
        ...                          ' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','0','1','2','3','4','5','6','7','8','9',' ','CLR','END']
        >>> entername_menu.visible = True
        >>> entername_menu.interactable = True
        ...
        >>> while True:                                                                             # Start our main game loop
        ...     if entername_menu.visible:
        ...
        ...         entername_menu.draw()                                                         # Draw the background menu
        ...         entername_menu.draw_textItem(entername_menu.letters, entername_menu.columns)  # Draw each individual selectable text item
        ...
        ...         if entername_menu.interactable:                                                 # Handle the user's input to update the selected menu item
        ...             entername_menu.update_menu_selection(pygame.event.get(), core.control.Control, input_allowed=True)


        .. image:: images/menu/update_menu_selections.png


        """

        # Only handle user input only if this menu is interactable
        if not self.interactable:
            return False

        # If the down key was pressed, move our selection down.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:

            self.selected_menu_item += self.columns
            if self.selected_menu_item > len(self.menu_items) -1:

                self.selected_menu_item -= self.selected_row * self.columns

            #self.menu_select_sound.play()
            logger.debug("Selected item: " + str(self.selected_menu_item))


        # If the up key was pressed, move our selection up.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:

            # Get the total number of rows based on the number of items divided by the number of columns
            total_rows = len(self.menu_items) / self.columns

            if (self.selected_menu_item) - self.columns < 0:
                self.selected_menu_item += self.columns * total_rows

                # If we overshot the size of the menu items, go up a row
                if self.selected_menu_item > len(self.menu_items) - 1:
                    self.selected_menu_item -= self.columns

            else:
                self.selected_menu_item -= self.columns

            #self.menu_select_sound.play()
            logger.debug("Selected item: " + str(self.selected_menu_item))


        # If the right key was pressed, move our selection to the right.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:

            # If the next selected menu item is PERFECTLY divisble by the product of the number of
            # columns times the selected row, then we need to go BACK to the beginning of the row
            # instead of selecting the next menu item
            if (self.selected_menu_item + 1) % (self.columns * self.selected_row) == 0:
                self.selected_menu_item -= self.columns - 1

            else:
                self.selected_menu_item += 1
                if self.selected_menu_item > len(self.menu_items) - 1:
                    self.selected_menu_item = 0


        # If the left key was pressed, move our selection to the left.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:

            # If the previos selected menu item is PERFECTLY divisble by the product of the number
            # of columns times the previous selected row, then we need to go BACK to the beginning
            # of the row instead of selecting the previous menu item
            if ((self.columns * (self.selected_row - 1)) > 0
                and (self.selected_menu_item) % (self.columns * (self.selected_row - 1)) == 0):
                self.selected_menu_item += self.columns - 1

            # If we're not at the start of the row, simply select the previous menu item
            else:
                self.selected_menu_item -= 1

                # If our selection is going to be less than zero, select the right-most item
                # in this row instead
                if self.selected_menu_item < 0:
                    #self.selected_menu_item = len(self.menu_items) - 1
                    self.selected_menu_item = self.columns - 1


        # Handle the player pressing ENTER on one of the selected letters.
        if input_allowed and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:

            # If the "CLR" button was selected, delete the last character from our name
            if self.menu_items[self.selected_menu_item] == "CLR":
                self.name = self.name[:-1]
                logger.debug("CLR pressed")
                logger.debug("Current Name: " + self.name)

            # If the "END" button was selected, close this menu and return the entered name.
            elif self.menu_items[self.selected_menu_item] == "END":
                logger.debug("Enter name menu completed")
                logger.debug("Current Input: " + self.input)
                self.visible = False
                self.interactable = False

            # For all other selected letters, append it to our name, if it has not exceeded our
            # name limit.
            else:
                if len(self.input) < self.input_max_size:
                    self.input += self.menu_items[self.selected_menu_item]
                else:
                    logger.debug("Input character limit reached")

                logger.debug("Current Input: " + self.input)


        # Set our selected row based on the number of columns we have and what item we have
        # selected
        self.selected_row = (self.selected_menu_item / self.columns) + 1



    def scale_sides(self):
        """Scales the border images of this menu instance to fit the size of the menu.

        :param: None

        :rtype: None
        :returns: None

        """
        #print(self.border["right"].get_width(), self.size_y)
        self.border["right"] = pygame.transform.scale(
            self.border["right"], (self.border["right"].get_width(), int(self.size_y)))
        self.border["left"] = pygame.transform.scale(
            self.border["left"], (self.border["left"].get_width(), int(self.size_y)))
        self.border["top"] = pygame.transform.scale(
            self.border["top"], (int(self.size_x), self.border["top"].get_height()))
        self.border["bottom"] = pygame.transform.scale(
            self.border["bottom"], (int(self.size_x), self.border["bottom"].get_height()))

        # If a background was specified, scale it to fit the size of the menu.
        if self.background:
            self.background = pygame.transform.scale(
                self.background, (self.size_x, self.size_y))


    def set_font(self, size=14, font="resources/font/PressStart2P.ttf", color=(10, 10, 10), spacing=10):
        """Set the font properties that the menu uses including font color, size, typeface,
        and line spacing.

        :param size: The font size in pixels
        :param font: Path to the typeface file (.ttf)
        :param color: A tuple of the RGB color values
        :param spacing: The spacing in pixels between lines of text

        :type size: Integer
        :type font: String
        :type color: Tuple
        :type spacing: Integer

        :rtype: None
        :returns: None

        This example shows how you can use the set_font() method to change the color and size of
        the drawn text.

        >>> menu = core.components.menu.Menu(screen, resolution)
        >>> menu.set_font(size=24, color=(255, 0, 0))
        >>>
        >>> while True:                         # Start our main game loop
        ...     menu.draw()                   # Draw the menu background and borders
        ...     menu.draw_text("SUCH FONT")   # Draw text

        .. image:: images/menu/set_font.png

        """
        if size < self.min_font_size:
            size = self.min_font_size
        self.font_size = size
        self.font = pygame.font.Font(font, self.font_size)
        self.font_color = color
        self.line_spacing = spacing

    def clicked(self, mouse_pos):
        print("Do nothing")


    def draw_button(self, text, mouse_pos):
        print("Button!")


    def draw_textItem(self, textlist, columns=1, pos_x=0, pos_y=0, align="middle", autoline_spacing=False, paging=False):
        """Draws selectable menu items to the window. Menu items are automatically centered based
        on the number of columns specified.

        :param textlist: A list of strings to draw to the window.
        :param columns: The number of items to display in each row. * Default: 1*
        :param pos_x: Start drawing the items at position x relative to the menu's position.
            *Default: 0*
        :param pos_y: Start drawing the items at position y relative to the menu's position.
            *Default: 0*
        :param align: Align the text items to the top, middle, or bottom of the menu. Valid
            options: "top", "middle", "bottom". *Default: "middle"*
        :param autoline_spacing: True or false value on whether or not to autmatically space the
            rows based on window size.
        :param paging: True or false value on whether or not to separate the list of items into
            pages if all the items can't fit on one screen.

        :type textlist: List
        :type columns: Integer
        :type pos_x: Integer
        :type pos_y: Integer
        :type align: String
        :type autoline_spacing: Boolean
        :type paging: Boolean

        :rtype: None
        :returns: None

        """
        #if len(self.menu_items) < 1:
        #    self.menu_items = textlist
        self.menu_items = textlist
        self.columns = columns

        # If the our list of menu items is now SHORTER than it was before, and our
        # "selected_menu_item" number exceeds the size of our list, set our selection to the
        # last item.
        if self.selected_menu_item > len(self.menu_items) - 1:
            self.selected_menu_item = len(self.menu_items) - 1


        # Do nothing if the text list is empty
        if not textlist:
            return False

        text_surfaceList = []	# This is the list of text surfaces to blit
        # Here we create an empty list that will contain lists of menu items sorted
        # into the appropriate number of columns. For example, if 3 columns are specified
        # then the list will look like this: [['Test', 'Testie', 'dick'], ['ass']]
        text_lists = []

        # Here we create an empty list to keep track of the current set of menu items we're
        # looking at.
        current_list = []

        # Loop through all the words in the list that was provided and add them to the text_lists
        # if we've reached the number of columns. This will give us a list that has a length of x
        # where "x" is the number of columns specified.
        for text in textlist:
            if len(current_list) >= columns:
                text_lists.append(current_list)
                current_list = []
                current_list.append(text)
            else:
                current_list.append(text)

        # If we've come to the last menu item in the list and we don't have an empty list, append
        # it to the text_lists.
        if current_list:
            text_lists.append(current_list)


        current_surface_list = []

        # Now we loop through each row
        for list in text_lists:

            # Now we loop through each column within that individual row
            for item in list:
                # Create a surface from the supplied word so we can draw it to the screen and
                # append it to the surface list.
                current_surface_list.append(self.font.render(item, 1, self.font_color))

            text_surfaceList.append(current_surface_list)
            current_surface_list = []

        # Here we're going to find the longest word out of all of the menu items so we know how to
        # format the columns. First we'll just set the first surface as the longest item and then
        # loop through the rest to see if they're longer.
        longest_item = text_surfaceList[0][0]

        # Here we loop through each surface and check its width in pixels. If it's longer than the
        # current one we're looking at, then make it the longest item
        for surfaceList in text_surfaceList:
            for surface in surfaceList:
                if surface.get_width() > longest_item.get_width():
                    longest_item = surface

        # Generate the space between the columns based on the longest item in our text
        self.column_spacing = (self.size_x - ((longest_item.get_width() * self.columns))) / (self.columns + 1)

        # If autoline spacing was specified, set our line spacing based on the size of our menu.
        if autoline_spacing:
            line_spacing = int(self.size_y / (len(textlist) / self.columns)) - longest_item.get_height()
        else:
            line_spacing = self.line_spacing

        if self.menuitempositions == False:
            self.menudis_x = self.column_spacing
            #self.menudis_y = longest_item.get_height()
            self.menudis_y = line_spacing/2

        # Keep track of the original "x" position so we can reset the value back every time we
        # loop through a row
        orig_x = self.menudis_x

        # Keep track of the item number so we can see if it is selected or not
        item_num = 0

        # Get the total number of lines we're going to be drawing to the screen
        number_of_lines = len(text_surfaceList)

        # If we specified paging, check to see how many rows will fit on a single page.
        if paging:

            # Get the total size in pixels of all the text plus line spacing we're going to draw.
            content_size = pos_y + (longest_item.get_height() * number_of_lines) + (line_spacing * number_of_lines)

            # Divide the size of the content in pixels by the size of the window to determine how
            # many pages we'll need.
            number_of_pages = math.ceil(float(content_size) / float(self.size_y))

            # Get the number of lines we'll be drawing per page.
            lines_per_page = math.floor(float(number_of_lines) / float(number_of_pages))

            # If our calculated number of lines per page and number of pages is
            # LESS than our actual number of lines, add an additional page.
            # This usually occurs if an odd number of items was specified.
            if (lines_per_page * number_of_pages) < number_of_lines:
                number_of_pages += 1

            # Loop through our list of rows we're going to draw and separate them into pages.
            pages = []
            current_lines = 1
            current_page = []
            for line in text_surfaceList:
                if current_lines <= lines_per_page:
                    current_page.append(line)
                    current_lines += 1
                else:
                    pages.append(current_page)
                    current_page = [line]
                    current_lines = 2

            # If we have a page left over, add it to our pages.
            if current_page:
                pages.append(current_page)

            # >>> pages
            # [[[<Surface(120x21x32 SW)>]], [[<Surface(240x21x32 SW)>]]]

            # Find out what page we're on based on our current menu selection.
            page_number = 1

            for line_number in range(1, int(number_of_lines + 1)):

                if line_number > (page_number * lines_per_page):
                    page_number += 1
                if line_number == int(self.selected_menu_item + 1):
                    break

            text_surfaceList = pages[page_number - 1]


        # Loop through the rows and blit the menu items to the screen
        for row in text_surfaceList:

            # Loop through each item in the row and blit it to the screen
            for item in row:

                icon_width = 0
                icon_height = 0

                # If we have an icon associated with this menu item, blit it as well
                if self.menu_icons:
                    self.screen.blit(
                        self.menu_icons[item_num],
                        ((self.pos_x + pos_x + (self.menudis_x) - (self.menu_icons[item_num].get_width()/1.5)),
                        (self.pos_y + pos_y + self.menudis_y - (self.menu_icons[item_num].get_height()/2))))

                    icon_width = self.menu_icons[item_num].get_width()
                    icon_height = self.menu_icons[item_num].get_height()

                self.screen.blit(item,
                    ((self.pos_x + pos_x + (self.menudis_x) + (icon_width / 2)),
                     (self.pos_y + pos_y + self.menudis_y)))

                # Draw the selection arrow if an item is selected
                if not paging and self.selected_menu_item == item_num:
                    self.screen.blit(self.arrow,
                        ((self.pos_x + pos_x + self.menudis_x ) - (self.arrow.get_width() * 1.3),
                         (self.pos_y + pos_y + self.menudis_y - (self.arrow.get_height() / 2) + (item.get_height() /2) ) ))

                # If paging is enabled, draw the selection arrow next to the selected menu item
                # based on the page we're on.
                elif paging:
                    # Get the ACTUAL selected menu item number by multiplying the page number
                    # we're on by the number of lines per page.
                    paged_selection_number = int(item_num + ((page_number - 1) * lines_per_page))

                    # If we're currently drawing the selected menu item, draw the arrow next to it.
                    if self.selected_menu_item == paged_selection_number:
                        self.screen.blit(self.arrow,
                            ((self.pos_x + pos_x + self.menudis_x ) - (self.arrow.get_width() * 1.3),
                             (self.pos_y + pos_y + self.menudis_y - (self.arrow.get_height() / 2) + (item.get_height() /2) ) ))

                # Offset the "x" value so that the next item is blitted to the right of the
                # previous one
                self.menudis_x += self.column_spacing + longest_item.get_width()

                # Increment the item number so we can keep track of it
                item_num += 1

            # Reset the "x" value so that it's back to its original position for the next row.
            self.menudis_x = orig_x

            # Offset the "y" value by the height of the text plus the line spacing.
            self.menudis_y += line_spacing + longest_item.get_height()


    def get_event(self, event=None, game=None):

        """Run this function to process menu specific events (such as actions for a specific
        menu item). By default this function does nothing.

        :param event: -- An optional pygame event from pygame.event.get() passed by
            core.control.Control get_menu_event() or a custom funtion.
        :param game: -- An optional instance of the game itself so the variables can be directly
            manipulated if needed.

        :type events: List
        :type game: core.control.Control

        :rtype: None
        :returns: None

        """
        pass


#plugins = plugin.load_directory("core/components/menu")
import core.components.menu.main_menu
import core.components.menu.dialog_menu
import core.components.menu.bottom_menu
import core.components.menu.interface
import core.components.menu.item_menu
import core.components.menu.monster_menu
import core.components.menu.save_menu
import core.components.menu.interaction_menu
