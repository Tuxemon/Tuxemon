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
# core.tools Contains various tools such as scene manager and states.
#
"""This module contains the fundamental Control class and a prototype class
for States.  Also contained here are resource loading functions.
"""

import logging
import os
import pygame as pg
import pprint
from .components import config
from .components import controller
from .components import player
from .components import cli
from .components import event
from .components import rumble

# Try and import networking if it is available.
try:
    from neteria.server import NeteriaServer
    from .components.middleware import Controller

    # Enable logging for the server.
    import sys
    import logging
    neteria_logger = logging.getLogger('neteria.server')
    neteria_logger.setLevel(logging.DEBUG)
    log_hdlr = logging.StreamHandler(sys.stdout)
    log_hdlr.setLevel(logging.DEBUG)
    log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "
                                            "%(levelname)s - %(message)s"))
    neteria_logger.addHandler(log_hdlr)
    neteria_logger.info("Server Started")

except ImportError:
    NeteriaServer = None
    Controller = None

# Import the android module. If we can't import it, set it to None - this
# lets us test it, and check to see if we want android-specific behavior.
try:
    import android
except ImportError:
    android = None

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Control(object):
    """Control class for entire project. Contains the game loop, and contains
    the event_loop which passes events to States as needed. Logic for flipping
    states is also found here.

    :param caption: The window caption to use for the game itself.

    :type caption: String
    
    :rtype: None
    :returns: None

    """

    def __init__(self, caption):
        self.screen = pg.display.get_surface()
        self.caption = caption
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60.0
        self.show_fps = True
        self.current_time = 0.0
        self.keys = pg.key.get_pressed()
        self.state_dict = {}
        self.state_name = None
        self.state = None
        if NeteriaServer and Controller:
            self.network_events = []
            self.server = NeteriaServer(Controller(self))
            self.server.listen()
        else:
            self.server = None

        # Set up our game's configuration from the prepare module.
        self.config = config.Config()

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_engine = event.EventEngine()
        self.event_conditions = {}
        self.event_actions = {}
        self.event_persist = {}

        # Set up a variable that will keep track of currently playing music.
        self.current_music = {"status": "stopped", "song": None}

        # Keep track of animations that we will play.
        self.animations = {}

        # Create these Pygame event objects to simulate KEYDOWN and KEYUP
        # events for all the directional keys
        self.keyboard_events = {}
        self.keyboard_events["KEYDOWN"] = {}
        self.keyboard_events["KEYDOWN"]["up"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 111, 'key': 273, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["down"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 116, 'key': 274, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["left"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 113, 'key': 276, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["right"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 114, 'key': 275, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["enter"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 36, 'key': 13, 'unicode': u'\r', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["escape"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 9, 'key': 27, 'unicode': u'\x1b', 'mod': 4096})
        self.keyboard_events["KEYUP"] = {}
        self.keyboard_events["KEYUP"]["up"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 111, 'key': 273, 'mod': 4096})
        self.keyboard_events["KEYUP"]["down"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 116, 'key': 274, 'mod': 4096})
        self.keyboard_events["KEYUP"]["left"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 113, 'key': 276, 'mod': 4096})
        self.keyboard_events["KEYUP"]["right"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 114, 'key': 275, 'mod': 4096})
        self.keyboard_events["KEYUP"]["enter"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 36, 'key': 13, 'mod': 4096})
        self.keyboard_events["KEYUP"]["escape"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 9, 'key': 27, 'mod': 4096})


        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False   # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

        # Controller overlay
        if self.config.controller_overlay == "1":
            self.controller = controller.Controller(self)
            self.controller.load()

        # Set up rumble support for gamepads
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler


    def setup_states(self, state_dict, start_state):
        """Given a dictionary of States and a State to start in,
        builds the self.state_dict.

        :param state_dict: A dictionary of core.tools._State objects.
        :param start_state: A string of the starting state. E.g. "START"

        :type state_dict: Dictionary
        :type start_state: String
    
        :rtype: None
        :returns: None

        **Examples:**

        >>> state_dict
        {'COMBAT': <core.states.combat.Combat object at 0x7f681d736590>,
         'START': <core.states.start.StartScreen object at 0x7f68230f5150>,
         'WORLD': <core.states.world.World object at 0x7f68230f54d0>}
        >>> start_state
        "START"

        """

        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]


    def update(self, dt):
        """Checks if a state is done or has called for a game quit.
        State is flipped if neccessary and State.update is called. This
        also calls the currently active state's "update" function each
        frame.

        :param dt: Time delta - Amount of time passed since last frame.

        :type dt: Float

        :rtype: None
        :returns: None

        **Example:**

        >>> dt
        0.031

        """

        self.current_time = pg.time.get_ticks()
        if self.state.quit:
            self.done = True
            self.exit = True
        elif self.state.done:
            self.flip_state()
        self.state.update(self.screen, self.keys, self.current_time, dt)
        if self.config.controller_overlay == "1":
            self.controller.draw(self)


    def flip_state(self):
        """When a State changes to "done" necessary startup and cleanup functions
        are called and the current State is changed. In addition, the state
        specified in self.state.next is loaded.

        :param None:

        :rtype: None
        :returns: None

        """

        previous, self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, persist)
        self.state.previous = previous


    def event_loop(self):
        """Process all events and pass them down to current State.  The F5 key
        globally turns on/off the display of FPS in the caption

        :param None:

        :rtype: None
        :returns: None

        """

        # Loop through our pygame events and pass them to the current state.
        self.keys = list(pg.key.get_pressed())
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
                self.exit = True

            elif event.type == pg.KEYDOWN:
                self.toggle_show_fps(event.key)

            if self.config.controller_overlay == "1":
                self.mouse_pos = pg.mouse.get_pos()
                self.controller_event_loop(event)

            self.state.get_event(event)

        # Loop through our network events and pass them to the current state.
        if self.server:
            self.network_event_loop()


    def network_event_loop(self):
        """Process all network events from the mobile controller and pass them
        down to current State. All network events are converted to keyboard
        events for compatibility.

        :param None:

        :rtype: None
        :returns: None

        """
        for event_data in self.network_events:
            if event_data == "KEYDOWN:up":
                self.keys[pg.K_UP] = 1
                event = self.keyboard_events["KEYDOWN"]["up"]

            elif event_data == "KEYUP:up":
                self.keys[pg.K_UP] = 0
                event = self.keyboard_events["KEYUP"]["up"]

            elif event_data == "KEYDOWN:down":
                self.keys[pg.K_DOWN] = 1
                event = self.keyboard_events["KEYDOWN"]["down"]

            elif event_data == "KEYUP:down":
                self.keys[pg.K_DOWN] = 0
                event = self.keyboard_events["KEYUP"]["down"]

            elif event_data == "KEYDOWN:left":
                self.keys[pg.K_LEFT] = 1
                event = self.keyboard_events["KEYDOWN"]["left"]

            elif event_data == "KEYUP:left":
                self.keys[pg.K_LEFT] = 0
                event = self.keyboard_events["KEYUP"]["left"]

            elif event_data == "KEYDOWN:right":
                self.keys[pg.K_RIGHT] = 1
                event = self.keyboard_events["KEYDOWN"]["right"]

            elif event_data == "KEYUP:right":
                self.keys[pg.K_RIGHT] = 0
                event = self.keyboard_events["KEYUP"]["right"]

            elif event_data == "KEYDOWN:enter":
                self.keys[pg.K_RETURN] = 1
                event = self.keyboard_events["KEYDOWN"]["enter"]

            elif event_data == "KEYUP:enter":
                self.keys[pg.K_RETURN] = 0
                event = self.keyboard_events["KEYUP"]["enter"]

            elif event_data == "KEYDOWN:esc":
                self.keys[pg.K_ESCAPE] = 1
                event = self.keyboard_events["KEYDOWN"]["escape"]

            elif event_data == "KEYUP:esc":
                self.keys[pg.K_ESCAPE] = 0
                event = self.keyboard_events["KEYUP"]["escape"]

            else:
                print "Unknown network event."
                event = None

            self.state.get_event(event)
        self.network_events = []


    def controller_event_loop(self, event):
        """Process all events from the controller overlay and pass them down to
        current State. All controller overlay events are converted to keyboard
        events for compatibility. This is primarily used for the mobile version
        of Tuxemon.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :rtype: None
        :returns: None

        """
        events = []
        if (event.type == pg.MOUSEBUTTONDOWN
            and event.button == 1):

            if self.controller.dpad["rect"]["up"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["up"])
                self.keys[pg.K_UP] = 1
            if self.controller.dpad["rect"]["down"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["down"])
                self.keys[pg.K_DOWN] = 1
            if self.controller.dpad["rect"]["left"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["left"])
                self.keys[pg.K_LEFT] = 1
            if self.controller.dpad["rect"]["right"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["right"])
                self.keys[pg.K_RIGHT] = 1

            if self.controller.a_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["enter"])
                self.keys[pg.K_RETURN] = 1
            if self.controller.b_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["escape"])
                self.keys[pg.K_ESCAPE] = 1


        if (event.type == pg.MOUSEBUTTONUP) and (event.button == 1):
            events.append(self.keyboard_events["KEYUP"]["up"])
            events.append(self.keyboard_events["KEYUP"]["down"])
            events.append(self.keyboard_events["KEYUP"]["left"])
            events.append(self.keyboard_events["KEYUP"]["right"])
            events.append(self.keyboard_events["KEYUP"]["enter"])
            self.keys[pg.K_RETURN] = 0
            events.append(self.keyboard_events["KEYUP"]["escape"])

        for event in events:
            self.state.get_event(event)


    def joystick_event_loop(self, event):
        """Process all events from a joystick and pass them down to
        current State. All joystick events are converted to keyboard
        events for compatibility.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :rtype: None
        :returns: None

        """
        from core import prepare

        # Handle joystick events if we detected one
        events = []
        if len(prepare.JOYSTICKS) > 0:

            # Xbox 360 Controller buttons:
            # A = 0    Start = 7    D-Up = 13
            # B = 1    Back = 6     D-Down = 14
            # X = 2                 D-Left = 11
            # Y = 3                 D-Right = 12
            #
            if event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["enter"])
                    self.keys[pg.K_RETURN] = 1
                if (event.button == 1
                    or event.button == 7 or event.button == 6):
                    events.append(
                        self.keyboard_events["KEYDOWN"]["escape"])
                    self.keys[pg.K_ESCAPE] = 1

                if event.button == 13:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["up"])
                    self.keys[pg.K_UP] = 1
                if event.button == 14:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["down"])
                    self.keys[pg.K_DOWN] = 1
                if event.button == 11:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["left"])
                    self.keys[pg.K_LEFT] = 1
                if event.button == 12:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["right"])
                    self.keys[pg.K_RIGHT] = 1

            elif event.type == pg.JOYBUTTONUP:
                if event.button == 0:
                    events.append(
                        self.keyboard_events["KEYUP"]["enter"])
                if (event.button == 1
                    or event.button == 7 or event.button == 6):
                    events.append(
                        self.keyboard_events["KEYUP"]["escape"])

                if event.button == 13:
                    events.append(self.keyboard_events["KEYUP"]["up"])
                if event.button == 14:
                    events.append(
                        self.keyboard_events["KEYUP"]["down"])
                if event.button == 11:
                    events.append(
                        self.keyboard_events["KEYUP"]["left"])
                if event.button == 12:
                    events.append(
                        self.keyboard_events["KEYUP"]["right"])

            # Handle left joystick movement as well.
            # Axis 1 - up = negative, down = positive
            # Axis 0 - left = negative, right = positive
            if event.type == pg.JOYAXISMOTION and False:    # Disabled until input manager is implemented

                # Handle the left/right axis
                if event.axis == 0:
                    if event.value >= 0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["right"])
                        self.keys[pg.K_RIGHT] = 1
                    elif event.value <= -0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["left"])
                        self.keys[pg.K_LEFT] = 1
                    else:
                        events.append(
                            self.keyboard_events["KEYUP"]["left"])
                        events.append(
                            self.keyboard_events["KEYUP"]["right"])

                # Handle the up/down axis
                if event.axis == 1:
                    if event.value >= 0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["down"])
                        self.keys[pg.K_DOWN] = 1
                    elif event.value <= -0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["up"])
                        self.keys[pg.K_LEFT] = 1
                    else:
                        events.append(
                            self.keyboard_events["KEYUP"]["up"])
                        events.append(
                            self.keyboard_events["KEYUP"]["down"])


    def toggle_show_fps(self, key):
        """Press f5 to turn on/off displaying the framerate in the caption.

        :param key: A pygame key event from pygame.event.get()

        :type key: PyGame Event

        :rtype: None
        :returns: None

        """

        if key == pg.K_F5:
            self.show_fps = not self.show_fps
            if not self.show_fps:
                pg.display.set_caption(self.caption)


    def main(self):
        """Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.tools.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.

        :param None:

        :rtype: None
        :returns: None

        """

        # This sets up Asteria networking to handle executing the game loop
        #listen(Controller(self), self, port=8000, game_loop=True)
        while not self.exit:
            self.main_loop()


    def main_loop(self):
        """Main loop for entire game. This method gets execute every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :param None:

        :rtype: None
        :returns: None

        """

        # Android-specific check for pause
        if android:
            if android.check_pause():
                android.wait_for_resume()

        # Get the amount of time that has passed since the last frame.
        time_delta = self.clock.tick(self.fps)/1000.0
        self.time_passed_seconds = time_delta
        self.event_loop()

        # Run our event engine which will check to see if game conditions
        # are met and run an action associated with that condition.
        self.event_data = {}
        self.event_engine.check_conditions(self)
        logger.debug("Event Data:" + str(self.event_data))

        # Draw and update our display
        self.update(time_delta)
        pg.display.update()
        if self.show_fps:
            fps = self.clock.get_fps()
            with_fps = "{} - {:.2f} FPS".format(self.caption, fps)
            pg.display.set_caption(with_fps)
        if self.exit:
            self.done = True


class _State(object):
    """This is a prototype class for States.  All states should inherit from it.
    No direct instances of this class should be created. get_event and update
    must be overloaded in the child class.  startup and cleanup need to be
    overloaded when there is data that must persist between States.

    """
    def __init__(self):
        self.start_time = 0.0
        self.current_time = 0.0
        self.done = False
        self.quit = False
        self.next = None
        self.previous = None
        self.persist = {}


    def get_event(self, event):
        """Processes events that were passed from the main event loop.
        Must be overridden in children.
        
        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None
        
        """
        pass


    def startup(self, current_time, persistant):
        """Add variables passed in persistant to the proper attributes and
        set the start time of the State to the current time.
        
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
        
        self.persist = persistant
        self.start_time = current_time


    def shutdown(self):
        """Called when State.done is set to True.
        
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
        pass


    def cleanup(self):
        """Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        
        :param None:

        :rtype: Dictionary
        :returns: Persist dictionary of variables.
        
        """
        self.done = False
        self.shutdown()
        return self.persist


    def update(self, surface, keys, current_time):
        """Update function for state.  Must be overloaded in children.
        
        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer 

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
        pass


    def render_font(self, font, msg, color, center):
        """Returns the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 1, color)
        rect = msg.get_rect(center=center)
        return msg, rect


### Resource loading functions.
def load_all_gfx(directory,colorkey=(255,0,255),accept=(".png",".jpg",".bmp")):
    """Load all graphics with extensions in the accept argument.  If alpha
    transparency is found in the image the image will be converted using
    convert_alpha().  If no alpha transparency is detected image will be
    converted using convert() and colorkey will be set to colorkey."""
    graphics = {}
    for pic in os.listdir(directory):
        name,ext = os.path.splitext(pic)
        if ext.lower() in accept:
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            graphics[name]=img
    return graphics


def load_all_music(directory, accept=(".ogg", ".mdi")):
    """Create a dictionary of paths to music files in given directory
    if their extensions are in accept."""
    songs = {}
    for song in os.listdir(directory):
        name,ext = os.path.splitext(song)
        if ext.lower() in accept:
            songs[name] = os.path.join(directory, song)
    return songs


def load_all_fonts(directory, accept=(".ttf",)):
    """Create a dictionary of paths to font files in given directory
    if their extensions are in accept."""
    return load_all_music(directory, accept)


def load_all_movies(directory, accept=(".mpg",)):
    """Create a dictionary of paths to movie files in given directory
    if their extensions are in accept."""
    return load_all_music(directory, accept)


def load_all_sfx(directory, accept=(".ogg", ".mdi")):
    """Load all sfx of extensions found in accept.  Unfortunately it is
    common to need to set sfx volume on a one-by-one basis.  This must be done
    manually if necessary in the setup module."""
    effects = {}
    for fx in os.listdir(directory):
        name,ext = os.path.splitext(fx)
        if ext.lower() in accept:
            effects[name] = pg.mixer.Sound(os.path.join(directory, fx))
    return effects


def strip_from_sheet(sheet, start, size, columns, rows=1):
    """Strips individual frames from a sprite sheet given a start location,
    sprite size, and number of columns and rows."""
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def strip_coords_from_sheet(sheet, coords, size):
    """Strip specific coordinates from a sprite sheet."""
    frames = []
    for coord in coords:
        location = (coord[0]*size[0], coord[1]*size[1])
        frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def get_cell_coordinates(rect, point, size):
    """Find the cell of size, within rect, that point occupies."""
    cell = [None, None]
    point = (point[0]-rect.x, point[1]-rect.y)
    cell[0] = (point[0]//size[0])*size[0]
    cell[1] = (point[1]//size[1])*size[1]
    return tuple(cell)


def cursor_from_image(image):
    """Take a valid image and create a mouse cursor."""
    colors = {(0,0,0,255) : "X",
              (255,255,255,255) : "."}
    rect = image.get_rect()
    icon_string = []
    for j in range(rect.height):
        this_row = []
        for i in range(rect.width):
            pixel = tuple(image.get_at((i,j)))
            this_row.append(colors.get(pixel, " "))
        icon_string.append("".join(this_row))
    return icon_string
