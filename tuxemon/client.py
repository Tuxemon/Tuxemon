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
from __future__ import annotations
import logging
import os.path
import time

import pygame as pg

from tuxemon.platform.platform_pygame.events import (
    PygameEventQueueHandler,
    PygameKeyboardInput,
    PygameGamepadInput,
    PygameMouseInput,
    PygameTouchOverlayInput,
)
from tuxemon import cli, networking, prepare
from tuxemon import rumble
from tuxemon.event.eventengine import EventEngine
from tuxemon.session import local_session
from tuxemon.state import StateManager, State
from tuxemon.map import TuxemonMap
from tuxemon.platform.events import PlayerInput
from typing import Iterable, Generator, Optional, Tuple, Mapping, Any


logger = logging.getLogger(__name__)


class Client(StateManager):
    """
    Client class for entire project.

    Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    Parameters:
        caption: The window caption to use for the game itself.

    """

    def __init__(self, caption: str) -> None:

        # Set up our game's configuration from the prepare module.
        self.config = config = prepare.CONFIG

        # INFO: no need to call superclass for now
        self.screen = pg.display.get_surface()
        self.caption = caption
        self.done = False
        self.fps = config.fps
        self.show_fps = config.show_fps
        self.current_time = 0.0
        self.ishost = False
        self.isclient = False

        # somehow this value is being patched somewhere
        self.events = list()
        self.inits = list()
        self.interacts = list()

        # TODO: move out to state manager
        self.package = "tuxemon.states"
        self._state_queue = list()
        self._state_dict = dict()
        self._state_stack = list()
        self._state_resume_set = set()

        keyboard = PygameKeyboardInput(config.keyboard_button_map)
        gamepad = PygameGamepadInput(config.gamepad_button_map, config.gamepad_deadzone)
        self.input_manager = PygameEventQueueHandler()
        self.input_manager.add_input(0, keyboard)
        self.input_manager.add_input(0, gamepad)
        self.controller_overlay = None
        if config.controller_overlay:
            self.controller_overlay = PygameTouchOverlayInput(config.controller_transparency)
            self.controller_overlay.load()
            self.input_manager.add_input(0, self.controller_overlay)
        if not config.hide_mouse:
            self.input_manager.add_input(0, PygameMouseInput())

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Set up our networking for multiplayer.
        self.server = networking.TuxemonServer(self)
        self.client = networking.TuxemonClient(self)
        self.controller_server = None

        # Set up our combat engine and router.
        # self.combat_engine = CombatEngine(self)
        # self.combat_router = CombatRouter(self, self.combat_engine)

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_engine = EventEngine(local_session)
        self.event_conditions = {}
        self.event_actions = {}
        self.event_persist = {}

        # Set up a variable that will keep track of currently playing music.
        self.current_music = {"status": "stopped", "song": None, "previoussong": None}

        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False  # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

        # Set up our networked controller if enabled.
        if self.config.net_controller_enabled:
            self.controller_server = networking.ControllerServer(self)

        # Set up rumble support for gamepads
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler

    def load_map(self, map_data: TuxemonMap) -> None:
        """
        Load a map.

        Parameters:
            map_data: The map to load.

        """
        self.events = map_data.events
        self.inits = map_data.inits
        self.interacts = map_data.interacts
        self.event_engine.reset()
        self.event_engine.current_map = map_data

    def draw_event_debug(self) -> None:
        """
        Very simple overlay of event data.  Needs some love.

        """
        y = 20
        x = 4

        yy = y
        xx = x

        font = pg.font.Font(pg.font.get_default_font(), 15)
        for event in self.event_engine.partial_events:
            w = 0
            for valid, item in event:
                p = " ".join(item.parameters)
                text = f"{item.operator} {item.type}: {p}"
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

    def process_events(
        self,
        events: Iterable[PlayerInput],
    ) -> Generator[pg.event.Event, None, None]:
        """
        Process all events for this frame.

        Events are first sent to the active state.
        States can choose to keep the events or return them.
        If they are kept, no other state nor the event engine will get that
        event.
        If they are returned, they will be passed to the next state.
        Kept or returned, the state may process it.
        Eventually, if all states have returned the event, it will go to the
        event engine.
        The event engine also can keep or return the event.
        All unused events will be added to Client.key_events each frame.
        Conditions in the the event system can then check that list.

        States can "keep" events by simply returning None from
        State.process_event

        Parameters:
            events: Sequence of events.

        Yields:
            Unprocessed event.

        """
        game_event: Optional[PlayerInput]

        for game_event in events:
            if game_event:
                game_event = self._send_event(game_event)
                if game_event:
                    yield game_event

    def _send_event(
        self,
        game_event: PlayerInput,
    ) -> Optional[PlayerInput]:
        """
        Send event down processing chain

        Probably a poorly named method.  Beginning from top state,
        process event, then as long as a new event is returned from
        the state, the event will be processed by the next active
        state in the stack.

        The final destination for the event will be the event engine.

        Parameters:
            game_event: Event to process.

        Returns:
            The event if no state keeps it. If some state keeps the
            event then the return value is ``None``.

        """
        for state in self.active_states:
            game_event_returned = state.process_event(game_event)
            if game_event_returned is None:
                break
        else:
            game_event_returned = self.event_engine.process_event(game_event)

        return game_event_returned

    def main(self) -> None:
        """
        Initiates the main game loop.

        Since we are using Asteria networking to handle network events,
        we pass this session.Client instance to networking which in turn
        executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.

        """
        update = self.update
        draw = self.draw
        screen = self.screen
        flip = pg.display.update
        clock = time.time
        frame_length = 1.0 / self.fps
        time_since_draw = 0.0
        last_update = clock()
        fps_timer = 0.0
        frames = 0

        while not self.exit:
            clock_tick = clock() - last_update
            last_update = clock()
            time_since_draw += clock_tick
            update(clock_tick)
            if time_since_draw >= frame_length:
                time_since_draw -= frame_length
                draw(screen)
                if self.controller_overlay:
                    self.controller_overlay.draw(screen)
                flip()
                frames += 1

            fps_timer, frames = self.handle_fps(clock_tick, fps_timer, frames)
            time.sleep(0.001)

    def update(self, time_delta: float) -> None:
        """
        Main loop for entire game.

        This method gets update every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        Parameters:
            time_delta: Elapsed time since last frame.

        """
        # Android-specific check for pause
        # if android and android.check_pause():
        #     android.wait_for_resume()

        # Update our networking
        if self.controller_server:
            self.controller_server.update()

        if self.client.listening:
            self.client.update(time_delta)
            self.add_clients_to_map(self.client.client.registry)

        if self.server.listening:
            self.server.update()

        # get all the input waiting for use
        events = self.input_manager.process_events()

        # process the events and collect the unused ones
        events = list(self.process_events(events))

        # TODO: phase this out in favor of event-dispatch
        self.key_events = events

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

    def release_controls(self) -> None:
        """
        Send inputs which release held buttons/axis

        Use to prevent player from holding buttons while state changes.

        """
        events = self.input_manager.release_controls()
        self.key_events = list(self.process_events(events))

    def update_states(self, dt: float) -> None:
        """
        Checks if a state is done or has called for a game quit.

        Parameters:
            dt: Time delta - Amount of time passed since last frame.

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

    def draw(self, surface: pg.surface.Surface) -> None:
        """
        Draw all active states.

        Parameters:
            surface: Surface where the drawing takes place.

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
            if not state.transparent and state.rect == full_screen and not state.force_draw:
                break

        # draw from bottom up for proper layering
        for state in reversed(to_draw):
            state.draw(surface)

        if self.config.collision_map:
            self.draw_event_debug()

        if self.save_to_disk:
            filename = "snapshot%05d.tga" % self.frame_number
            self.frame_number += 1
            pg.image.save(self.screen, filename)

    def handle_fps(
        self,
        clock_tick: float,
        fps_timer: float,
        frames: int,
    ) -> Tuple[float, int]:
        """
        Compute and print the frames per second.

        This function only prints FPS if that option has been set in the
        config.
        In order to have a long enough time interval to accurately compute the
        FPS, it only prints the FPS if at least one second has elapsed since
        last time it printed them.

        Parameters:
            clock_tick: Seconds elapsed since the last ``update`` call.
            fps_timer: Number of seconds elapsed since the last time the FPS
                were printed.
            frames: Number of frames printed since the last time the FPS were
                printed.

        Returns:
            Updated values of ``fps_timer`` and ``frames``. They will be the
            same as the valued passed unless the FPS are printed, in wich case
            they are reset to 0.

        """
        if self.show_fps:
            fps_timer += clock_tick
            if fps_timer >= 1:
                with_fps = f"{self.caption} - {frames / fps_timer:.2f} FPS"
                pg.display.set_caption(with_fps)
                return 0, 0
            return fps_timer, frames
        return 0, 0

    def add_clients_to_map(self, registry: Mapping[str, Any]) -> None:
        """
        Add players in the current map as npcs.

        Checks to see if clients are supposed to be displayed on the current
        map. If they are on the same map as the host then it will add them to
        the npc's list. If they are still being displayed and have left the
        map it will remove them from the map.

        Parameters:
            registry: Locally hosted Neteria client/server registry.

        """
        world = self.get_state_by_name("WorldState")
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

    def get_map_filepath(self) -> Optional[str]:
        """
        Gets the filepath of the current map.

        Returns:
            File path of the current map, if there is one.

        """
        world = self.get_state_by_name("WorldState")
        if not world:
            return None

        return world.current_map.filename

    def get_map_name(self) -> Optional[str]:
        """
        Gets the name of the current map.

        Returns:
            Name of the current map, if there is one.

        """
        map_path = self.get_map_filepath()
        if map_path is None:
            return None

        # extract map name from path
        return os.path.basename(map_path)

    def get_state_by_name(self, name: str) -> Optional[State]:
        """
        Query the state stack for a state by the name supplied.

        Parameters:
            name: Name of a state.

        Returns:
            State with that name, if one exist. ``None`` otherwise.

        """
        for state in self.active_states:
            if state.__class__.__name__ == name:
                return state

        return None
