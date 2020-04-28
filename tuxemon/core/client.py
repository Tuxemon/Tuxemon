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
from __future__ import print_function
from __future__ import unicode_literals

import logging
import time

import pygame as pg

from tuxemon.core import cli, networking
from tuxemon.core.clock import Scheduler, Clock
from tuxemon.core.platform import android
from tuxemon.core.platform.platform_pygame.events import PygameEventQueueHandler
from tuxemon.core.state import StateManager

logger = logging.getLogger(__name__)


class LocalPygameClient(object):
    """ Client to play locally using pygame

    * Uses a state manger to handle game states
    * Uses pygame for input and output
    * Has a game window, requires a screen

    """

    def __init__(self, world, config):
        """ Constructor

        :param tuxemon.core.world.World world:
        :param tuxemon.core.config.TuxemonConfig config:
        """
        self.world = world
        self.config = config

        self.state_manager = StateManager()
        self.state_manager.auto_state_discovery()
        self.screen = pg.display.get_surface()
        self.input_manager = PygameEventQueueHandler()
        self.caption = config.window_caption
        self.running = False

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Set up our networking for multiplayer
        self.net_server = networking.TuxemonServer(self)
        self.net_client = networking.TuxemonClient(self)
        self.ishost = False
        self.isclient = False

        # Set up a variable that will keep track of currently playing music.
        self.current_music = {"status": "stopped", "song": None, "previoussong": None}

        # Set up the command line. This provides a full python shell for
        # troubleshooting and you can view and manipulate any variables.
        if self.config.cli:
            self.cli = cli.CommandLine(self)

        # TODO: phase this out in favor of event-dispatch
        self.key_events = list()

        self.push_state = self.state_manager.push_state

    def run(self):
        """ Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.session.Client instance to
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
        frame_length = 1.0 / self.config.fps
        time_since_draw = 0
        last_update = clock()
        fps_timer = 0
        frames = 0

        self.running = True
        while self.running:
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
            time.sleep(0.001)

        pg.quit()

    def stop(self):
        self.running = False

    def update(self, time_delta):
        """ This method gets updated at least once per frame

        :type time_delta: float
        :rtype: None
        :returns: None
        """
        # Android-specific check for pause
        if android and android.check_pause():
            android.wait_for_resume()

        # Update our networking
        if self.net_client.listening:
            self.net_client.update(time_delta)
        if self.net_server.listening:
            self.net_server.update()

        # get all the input waiting for use
        events = self.input_manager.process_events()

        # process the events and collect the unused ones
        events = list(self.process_events(events))
        self.key_events = events

        # Update the game engine
        self.world.update(time_delta)
        self.update_states(time_delta)

    def release_controls(self):
        """ Send inputs which release held buttons/axis

        Use to prevent player from holding buttons while state changes

        :return:
        """
        events = self.input_manager.release_controls()
        self.key_events = list(self.process_events(events))

    def draw(self, surface):
        """ Draw all active states

        :type surface: pg.surface.Surface
        """
        # TODO: refactor into Widget

        # iterate through layers and determine optimal drawing strategy
        # this is a big performance boost for states covering other states
        # force_draw is used for transitions, mostly
        to_draw = list()
        full_screen = surface.get_rect()
        for state in self.state_manager.active_states:
            to_draw.append(state)

            # if this state covers the screen
            # break here so lower screens are not drawn
            if (
                not state.transparent
                and state.rect == full_screen
                and not state.force_draw
            ):
                break

        # draw from bottom up for proper layering
        for state in reversed(to_draw):
            state.draw(surface)

        if self.save_to_disk:
            filename = "snapshot%05d.tga" % self.frame_number
            self.frame_number += 1
            pg.image.save(self.screen, filename)

    def handle_fps(self, clock_tick, fps_timer, frames):
        if self.config.show_fps:
            fps_timer += clock_tick
            if fps_timer >= 1:
                with_fps = "{} - {:.2f} FPS".format(self.caption, frames / fps_timer)
                pg.display.set_caption(with_fps)
                return 0, 0
            return fps_timer, frames
        return 0, 0

    def process_events(self, events):
        """ Process all events for this frame.

        Events are first sent to the active state.
        States can choose to keep the events or return them.
        If they are kept, no other state nor the event engine will get that event.
        If they are returned, they will be passed to the next state.
        Kept or returned, the state may process it.
        Eventually, if all states have returned the event, it will go to the event engine.
        The event engine also can keep or return the event.
        All unused events will be added to Client.key_events each frame.
        Conditions in the the event system can then check that list.

        States can "keep" events by simply returning None from State.process_event

        :param events: Sequence of pg events
        :returns: Iterator of game events
        :rtype: collections.Iterable[pg.event.Event]

        """
        for game_event in events:
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

        :rtype: pg.event.Event

        """
        for state in self.state_manager.active_states:
            game_event = state.process_event(game_event)
            if game_event is None:
                break
        else:
            logger.debug("got unhandled event: {}".format(game_event))
        return game_event

    def update_states(self, dt):
        """ Checks if a state is done or has called for a game quit.

        :param Float dt: Time delta - Amount of time passed since last frame
        """
        for state in self.state_manager.active_states:
            state.update(dt)

        current_state = self.state_manager.current_state

        # handle case where the top state has been dismissed
        if current_state is None:
            self.running = False

        if current_state in self.state_manager.state_resume_set:
            current_state.resume()
            self.state_manager.state_resume_set.remove(current_state)

    def get_state_by_name(self, name):
        """ Query the state stack for a state by the name supplied

        :str name: str
        :rtype: State, None
        """
        for state in self.state_manager.active_states:
            if state.__class__.__name__ == name:
                return state
        return None
