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
# Leif Theden <leif.theden@gmail.com>
#
from __future__ import absolute_import, division

import logging
import os.path
import time

import pygame as pg

import tuxemon.core.components.event.eventengine
from . import prepare
from .components import cli, controller, networking, rumble
from .components.game_event import GAME_EVENT
from .platform import android
from .state import StateManager

logger = logging.getLogger(__name__)


class Control(StateManager):
    """Control class for entire project. Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    :param caption: The window caption to use for the game itself.

    :type caption: String

    :rtype: None
    :returns: None

    """

    def __init__(self, caption):
        # Set up our game's configuration from the prepare module.
        self.config = prepare.CONFIG

        # INFO: no need to call superclass for now
        self.screen = pg.display.get_surface()
        self.caption = caption
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = self.config.fps
        self.show_fps = self.config.show_fps
        self.current_time = 0.0
        self.ishost = False
        self.isclient = False

        # somehow this value is being patched somewhere
        self.events = list()
        self.inits = list()
        self.interacts = list()

        # TODO: move out to state manager
        self.package = "tuxemon.core.states"
        self._state_queue = list()
        self._state_dict = dict()
        self._state_stack = list()
        self._state_resume_set = set()
        self._remove_queue = list()
        self._held_keys = list()

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Set up our networking for multiplayer.
        self.server = networking.TuxemonServer(self)
        self.client = networking.TuxemonClient(self)
        self.controller_server = None

        # Set up our combat engine and router.
        #        self.combat_engine = CombatEngine(self)
        #        self.combat_router = CombatRouter(self, self.combat_engine)

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_engine = tuxemon.core.components.event.eventengine.EventEngine(self)
        self.event_conditions = {}
        self.event_actions = {}
        self.event_persist = {}

        # Set up a variable that will keep track of currently playing music.
        self.current_music = {"status": "stopped", "song": None, "previoussong": None}

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
        self.exit = False  # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

        # Controller overlay
        if self.config.controller_overlay:
            self.controller = controller.Controller(self)
            self.controller.load()

            # Keep track of what buttons have been pressed when the overlay
            # controller is enabled.
            self.overlay_pressed = {
                "up": False,
                "down": False,
                "left": False,
                "right": False,
                "a": False,
                "b": False
            }

        # Set up our networked controller if enabled.
        if self.config.net_controller_enabled:
            self.controller_server = networking.ControllerServer(self)

        # Set up rumble support for gamepads
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler

        # TODO: moar players
        self.player1 = None

    def add_player(self, player):
        """ Add a player to the game

        Only one human player is supported ATM

        :type player: core.components.player.Player
        :return:
        """
        # TODO: moar players
        self.player1 = player

    def get_player(self):
        return self.player1

    def draw_event_debug(self):
        """ Very simple overlay of event data.  Needs some love.

        :return:
        """
        y = 20
        x = 4

        yy = y
        xx = x

        font = pg.font.Font(pg.font.get_default_font(), 15)
        for event in self.event_engine.partial_events:
            w = 0
            for valid, item in event:
                p = ' '.join(item.parameters)
                text = "{} {}: {}".format(item.operator, item.type, p)
                if valid:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)
                image = font.render(text, 1, color)
                self.screen.blit(image, (xx, yy))
                ww, hh = image.get_size()
                yy += hh
                w = max(w, ww)

            xx += w + 20

            if xx > 1000:
                xx = x
                y += 200

            yy = y

    def gather_events(self):
        """ Collect all platform input events and iterate them.

        No logic should be processed here.

        :returns: Iterator of game events
        :rtype: collections.Iterable[pygame.event.Event]

        """
        for pg_event in pg.event.get():
            # get system events
            for game_event in self.get_system_event(pg_event):
                yield game_event

            # get keyboard events
            for game_event in self.get_keyboard_event(pg_event):
                yield game_event

            # Loop through our controller overlay events
            if self.config.controller_overlay == "1":
                self.mouse_pos = pg.mouse.get_pos()
                for game_event in self.get_controller_event(pg_event):
                    yield game_event

            # Loop through normal mouse events
            if pg_event.type == pg.MOUSEBUTTONDOWN:
                yield pg_event

            # Loop through our joystick events
            for game_event in self.get_joystick_event(pg_event):
                yield game_event

            # Loop through our user defined events
            for game_event in self.get_user_event(pg_event):
                yield game_event

    def process_events(self, events):
        """ Process all events for this frame.

        Events are first sent to the active state.
        States can choose to keep the events or return them.
        If they are kept, no other state nor the event engine will get that event.
        If they are returned, they will be passed to the next state.
        Kept or returned, the state may process it.
        Eventually, if all states have returned the event, it will go to the event engine.
        The event engine also can keep or return the event.
        All unused events will be added to Control.key_events each frame.
        Conditions in the the event system can then check that list.

        States can "keep" events by simply returning None from State.process_event

        :param events: Sequence of pygame events
        :returns: Iterator of game events
        :rtype: collections.Iterable[pygame.event.Event]

        """
        for game_event in events:
            if game_event.type == pg.QUIT:
                # TODO: API
                self.done = True
                self.exit = True

            # keep track of held keys
            # when the state changes, keyup events will be sent to reset the controls
            elif game_event.type == pg.KEYDOWN:
                self._held_keys.append(game_event)
                self.toggle_show_fps(game_event.key)

            elif game_event.type == pg.KEYUP:
                # this will fail when a keypress changes state.
                match = [i for i in self._held_keys if i.key == game_event.key]
                if match:
                    for stale_event in match:
                        self._held_keys.remove(stale_event)
                else:
                    # prevent keyup events from leaking to next state
                    continue

            if game_event:
                game_event = self._send_event(game_event)

                if game_event:
                    yield game_event

    def _send_event(self, game_event):
        """ Send event down processing chain

        Probably a poorly named method.  Beginning from top state,
        process event, then as long as a new event is returned from
        the state, the event will be processed by the next active
        state in the stack.

        The final destination for the event will be the event engine.

        :returns: Game Event
        :rtype: pygame.event.Event

        """
        for state in self.active_states:
            game_event = state.process_event(game_event)
            if game_event is None:
                break
        else:
            game_event = self.event_engine.process_event(game_event)

        return game_event

    @staticmethod
    def get_system_event(game_event):
        """ Filter system events

        :param game_event: pygame.event.Event
        :returns: Iterator of game events
        :rtype: collections.Iterable[pygame.event.Event]

        """
        if game_event.type in [pg.QUIT]:
            yield game_event

    @staticmethod
    def get_keyboard_event(game_event):
        """ Translate a pygame event to an internal game event

        This is a transitional class.  Eventually a more robust
        events class will be used.

        :param game_event: pygame.event.Event
        :returns: Iterator of game events
        :rtype: collections.Iterable[pygame.event.Event]

        """
        if game_event.type in [pg.KEYUP, pg.KEYDOWN]:
            yield game_event

    def get_controller_event(self, event):
        """ Process all events from the controller overlay and pass them down to
        current State. All controller overlay events are converted to keyboard
        events for compatibility. This is primarily used for the mobile version
        of Tuxemon.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :returns: List of events
        :rtype: List

        """
        events = []
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:

            if self.controller.dpad["rect"]["up"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["up"])
                self.overlay_pressed["up"] = True
            if self.controller.dpad["rect"]["down"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["down"])
                self.overlay_pressed["down"] = True
            if self.controller.dpad["rect"]["left"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["left"])
                self.overlay_pressed["left"] = True
            if self.controller.dpad["rect"]["right"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["right"])
                self.overlay_pressed["right"] = True
            if self.controller.a_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["enter"])
                self.overlay_pressed["a"] = True
            if self.controller.b_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["escape"])
                self.overlay_pressed["b"] = True

        if (event.type == pg.MOUSEBUTTONUP) and (event.button == 1):
            if self.overlay_pressed["up"]:
                events.append(self.keyboard_events["KEYUP"]["up"])
                self.overlay_pressed["up"] = False
            if self.overlay_pressed["down"]:
                events.append(self.keyboard_events["KEYUP"]["down"])
                self.overlay_pressed["down"] = False
            if self.overlay_pressed["left"]:
                events.append(self.keyboard_events["KEYUP"]["left"])
                self.overlay_pressed["left"] = False
            if self.overlay_pressed["right"]:
                events.append(self.keyboard_events["KEYUP"]["right"])
                self.overlay_pressed["right"] = False
            if self.overlay_pressed["a"]:
                events.append(self.keyboard_events["KEYUP"]["enter"])
                self.overlay_pressed["a"] = False
            if self.overlay_pressed["b"]:
                events.append(self.keyboard_events["KEYUP"]["escape"])
                self.overlay_pressed["b"] = False

        return events

    def get_joystick_event(self, event):
        """ Process all events from a joystick and pass them down to
        current State. All joystick events are converted to keyboard
        events for compatibility.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :rtype: List
        :returns: List of events

        """

        # Handle joystick events if we detected one
        events = []
        append = events.append
        kbd_event = self.keyboard_events
        if prepare.JOYSTICKS:

            # Xbox 360 Controller buttons:
            # A = 0    Start = 7    D-Up = 13
            # B = 1    Back = 6     D-Down = 14
            # X = 2                 D-Left = 11
            # Y = 3                 D-Right = 12
            #
            if event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:
                    append(kbd_event["KEYDOWN"]["enter"])
                if event.button == 1 or event.button == 7 or event.button == 6:
                    append(kbd_event["KEYDOWN"]["escape"])

                if event.button == 13:
                    append(kbd_event["KEYDOWN"]["up"])
                if event.button == 14:
                    append(kbd_event["KEYDOWN"]["down"])
                if event.button == 11:
                    append(kbd_event["KEYDOWN"]["left"])
                if event.button == 12:
                    append(kbd_event["KEYDOWN"]["right"])

            elif event.type == pg.JOYBUTTONUP:
                if event.button == 0:
                    append(kbd_event["KEYUP"]["enter"])
                if event.button == 1 or event.button == 7 or event.button == 6:
                    append(kbd_event["KEYUP"]["escape"])

                if event.button == 13:
                    append(kbd_event["KEYUP"]["up"])
                if event.button == 14:
                    append(kbd_event["KEYUP"]["down"])
                if event.button == 11:
                    append(kbd_event["KEYUP"]["left"])
                if event.button == 12:
                    append(kbd_event["KEYUP"]["right"])

            # Handle left joystick movement as well.
            # Axis 1 - up = negative, down = positive
            # Axis 0 - left = negative, right = positive
            if event.type == pg.JOYAXISMOTION and False:  # Disabled until input manager is implemented

                # Handle the left/right axis
                if event.axis == 0:
                    if event.value >= 0.5:
                        append(kbd_event["KEYDOWN"]["right"])
                    elif event.value <= -0.5:
                        append(kbd_event["KEYDOWN"]["left"])
                    else:
                        append(kbd_event["KEYUP"]["left"])
                        append(kbd_event["KEYUP"]["right"])

                # Handle the up/down axis
                if event.axis == 1:
                    if event.value >= 0.5:
                        append(kbd_event["KEYDOWN"]["down"])
                    elif event.value <= -0.5:
                        append(kbd_event["KEYDOWN"]["up"])
                    else:
                        append(kbd_event["KEYUP"]["up"])
                        append(kbd_event["KEYUP"]["down"])

        return events

    @staticmethod
    def get_user_event(game_event):
        """ Filter user defined events

        :param game_event: pygame.event.Event
        :returns: Iterator of game events
        :rtype: collections.Iterable[pygame.event.Event]

        """
        if game_event.type in [GAME_EVENT]:
            yield game_event

    def toggle_show_fps(self, key):
        """ Press f5 to turn on/off displaying the framerate in the caption.

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
        to handle network events, we pass this core.control.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.

        :rtype: None
        :returns: None

        """
        update = self.update
        draw = self.draw
        screen = self.screen
        flip = pg.display.update
        clock = time.time
        frame_length = (1. / self.fps)
        time_since_draw = 0
        last_update = clock()
        fps_timer = 0
        frames = 0

        while not self.exit:
            clock_tick = clock() - last_update
            last_update = clock()
            time_since_draw += clock_tick
            update(clock_tick)
            if time_since_draw >= frame_length:
                time_since_draw -= frame_length
                draw(screen)
                flip()
                frames += 1

            fps_timer, frames = self.handle_fps(clock_tick, fps_timer, frames)

            time.sleep(.001)

    def update(self, time_delta):
        """Main loop for entire game. This method gets update every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :type time_delta: float
        :rtype: None
        :returns: None

        """
        # Android-specific check for pause
        if android and android.check_pause():
            android.wait_for_resume()

        # Update our networking.
        if self.controller_server:
            self.controller_server.update()

        if self.client.listening:
            self.client.update(time_delta)
            self.add_clients_to_map(self.client.client.registry)

        if self.server.listening:
            self.server.update()

        # get all the input waiting for use
        events = self.gather_events()

        # process the events and collect the unused ones
        events = self.process_events(events)

        # this attribute is used for the event engine __only__
        self.key_events = list(events)

        # Run our event engine which will check to see if game conditions
        # are met and run an action associated with that condition.
        self.event_data = {}
        self.event_engine.update(time_delta)

        if self.event_data:
            logger.debug("Event Data:" + str(self.event_data))

        # Update the game engine
        self.update_states(time_delta)

        if self.exit:
            self.done = True

    def update_states(self, dt):
        """ Checks if a state is done or has called for a game quit.

        :param dt: Time delta - Amount of time passed since last frame.

        :type dt: Float
        """

        for state in self.active_states:
            state.update(dt)

        current_state = self.current_state

        # handle case where the top state has been dismissed
        if current_state is None:
            self.exit = True

        if current_state in self._state_resume_set:
            current_state.resume()
            self._state_resume_set.remove(current_state)

    def draw(self, surface):
        """ Draw all active states

        :type surface: pygame.surface.Surface
        """
        # TODO: refactor into Widget

        # iterate through layers and determine optimal drawing strategy
        # this is a big performance boost for states covering other states
        # force_draw is used for transitions, mostly
        to_draw = list()
        full_screen = surface.get_rect()
        for state in self.active_states:
            to_draw.append(state)

            # if this state covers the screen
            # break here so lower screens are not drawn
            if (not state.transparent
                    and state.rect == full_screen
                    and not state.force_draw):
                break

        # draw from bottom up for proper layering
        for state in reversed(to_draw):
            state.draw(surface)

        if self.config.controller_overlay == "1":
            self.controller.draw(surface)

        if self.config.collision_map == "1":
            self.draw_event_debug()

        # if self.save_to_disk:
        #     filename = "snapshot%05d.tga" % self.frame_number
        #     self.frame_number += 1
        #     pg.image.save(self.screen, filename)

    def handle_fps(self, clock_tick, fps_timer, frames):
        if self.show_fps:
            fps_timer += clock_tick
            if fps_timer >= 1:
                with_fps = "{} - {:.2f} FPS".format(self.caption, frames / fps_timer)
                pg.display.set_caption(with_fps)
                return 0, 0
            return fps_timer, frames
        return 0, 0

    def add_clients_to_map(self, registry):
        """Checks to see if clients are supposed to be displayed on the current map. If
        they are on the same map as the host then it will add them to the npc's list.
        If they are still being displayed and have left the map it will remove them from
        the map.

        :param registry: Locally hosted Neteria client/server registry.

        :type registry: Dictionary

        :rtype: None
        :returns: None

        """
        world = self.get_state_name("WorldState")
        if not world:
            return

        world.npcs = {}
        world.npcs_off_map = {}
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if sprite.slug not in world.npcs:
                        world.npcs[sprite.slug] = sprite
                    if sprite.slug in world.npcs_off_map:
                        del world.npcs_off_map[sprite.slug]

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if sprite.slug not in world.npcs_off_map:
                        world.npcs_off_map[sprite.slug] = sprite
                    if sprite.slug in world.npcs:
                        del world.npcs[sprite]

    def get_map_name(self):
        """Gets the map of the player.

        :rtype: String
        :returns: map_name

        """
        world = self.get_state_name("WorldState")
        if not world:
            return

        map_path = world.current_map.filename

        # extract map name from path
        map_name = os.path.basename(map_path)

        return map_name

    def get_state_name(self, name):
        """ Query the state stack for a state by the name supplied

        :str name: str
        :rtype: State, None
        """
        for state in self.active_states:
            if state.__class__.__name__ == name:
                return state
        return None


class PygameControl(Control):
    pass


class HeadlessControl(Control, StateManager):
    """Control class for headless server. Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    :param: None
    :rtype: None
    :returns: None

    """

    def __init__(self):
        self.done = False

        self.clock = time.clock()
        self.fps = 60.0
        self.current_time = 0.0

        # TODO: move out to state manager
        self.package = "tuxemon.core.states"
        self.state_dict = dict()
        self._state_stack = list()

        self.server = networking.TuxemonServer(self)
        # self.server_thread = threading.Thread(target=self.server)
        # self.server_thread.start()
        self.server.server.listen()

        # Set up our game's configuration from the prepare module.
        self.config = prepare.HEADLESSCONFIG

        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False  # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

    def update(self):
        """Main loop for entire game. This method gets update every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :param None:

        :rtype: None
        :returns: None

        """
        # Get the amount of time that has passed since the last frame.
        # self.time_passed_seconds = time.clock() - self.clock
        # self.server.update()

        if self.exit:
            self.done = True

    def main(self):
        """Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.control.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.
        :param None:
        :rtype: None
        :returns: None
        """
        while not self.exit:
            self.update()
