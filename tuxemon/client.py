# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os.path
import time
from collections.abc import Generator, Iterable, Mapping, Sequence
from threading import Thread
from typing import Any, Optional, TypeVar, Union, overload

import pygame as pg

from tuxemon import networking, prepare, rumble
from tuxemon.audio import MusicPlayerState, SoundManager
from tuxemon.cli.processor import CommandProcessor
from tuxemon.config import TuxemonConfig
from tuxemon.db import MapType
from tuxemon.event import EventObject
from tuxemon.event.eventengine import EventEngine
from tuxemon.map import TuxemonMap
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.input_manager import InputManager
from tuxemon.session import local_session
from tuxemon.state import State, StateManager
from tuxemon.states.world.worldstate import WorldState

StateType = TypeVar("StateType", bound=State)

logger = logging.getLogger(__name__)


class LocalPygameClient:
    """
    Client class for entire project.

    Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    Parameters:
        config: The config for the game.

    """

    def __init__(
        self, config: TuxemonConfig, screen: pg.surface.Surface
    ) -> None:
        self.config = config

        self.state_manager = StateManager(
            "tuxemon.states",
            on_state_change=self.on_state_change,
        )
        self.state_manager.auto_state_discovery()
        self.screen = screen
        self.caption = config.window_caption
        self.done = False
        self.fps = config.fps
        self.show_fps = config.show_fps
        self.current_time = 0.0

        # somehow this value is being patched somewhere
        self.events: Sequence[EventObject] = []
        self.inits: list[EventObject] = []

        # setup controls
        self.input_manager = InputManager(config)

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Set up our networking for multiplayer.
        self.network_manager = networking.NetworkManager(self)
        self.network_manager.initialize()

        # Set up our combat engine and router.
        # self.combat_engine = CombatEngine(self)
        # self.combat_router = CombatRouter(self, self.combat_engine)

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_engine = EventEngine(local_session)
        self.event_persist: dict[str, dict[str, Any]] = {}

        # Set up a variable that will keep track of currently playing music.
        self.current_music = MusicPlayerState()
        self.sound_manager = SoundManager()

        if self.config.cli:
            # TODO: There is no protection for the main thread from the cli
            # actions that execute in this thread may have undefined
            # behavior for the game.  at some point, a lock should be
            # implemented so that actions executed here have exclusive
            # control of the game loop and state.
            self.cli = CommandProcessor(local_session)
            thread = Thread(target=self.cli.run)
            thread.daemon = True
            thread.start()

        # Set up rumble support for gamepads
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler

        # TODO: phase these out
        self.key_events: Sequence[PlayerInput] = []
        self.event_data: dict[str, Any] = {}
        self.exit = False

    def on_state_change(self) -> None:
        logger.debug("resetting controls due to state change")
        self.release_controls()

    def load_map(self, map_data: TuxemonMap) -> None:
        """
        Load a map.

        Parameters:
            map_data: The map to load.

        """
        self.events = map_data.events
        self.inits = list(map_data.inits)
        self.event_engine.reset()
        self.event_engine.current_map = map_data
        self.maps = map_data.maps

        # Map properties
        self.map_slug = map_data.slug
        self.map_name = map_data.name
        self.map_desc = map_data.description
        self.map_inside = map_data.inside
        self.map_area = map_data.area
        self.map_size = map_data.size

        # Check if the map type exists
        self.map_type = MapType.notype
        if map_data.map_type in list(MapType):
            self.map_type = MapType(map_data.map_type)
        else:
            logger.warning(
                f"The type '{map_data.map_type}' doesn't exist."
                f"By default assigned {MapType.notype}!"
            )

        # Cardinal points
        self.map_north = map_data.north_trans
        self.map_south = map_data.south_trans
        self.map_east = map_data.east_trans
        self.map_west = map_data.west_trans

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
                    color = prepare.GREEN_COLOR
                else:
                    color = prepare.RED_COLOR
                image = font.render(text, True, color)
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
    ) -> Generator[PlayerInput, None, None]:
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

        Conditions in the event system can then check that list.
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
            _game_event = state.process_event(game_event)
            if _game_event is None:
                break
            return _game_event
        return None

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
                if self.input_manager.controller_overlay:
                    self.input_manager.controller_overlay.draw(screen)
                flip()
                frames += 1

            fps_timer, frames = self.handle_fps(clock_tick, fps_timer, frames)
            time.sleep(0.01)

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
        # Update our networking
        self.network_manager.update(time_delta)

        # get all the input waiting for use
        events = self.input_manager.process_events()

        # process the events and collect the unused ones
        key_events = list(self.process_events(events))

        # TODO: phase this out in favor of event-dispatch
        self.key_events = key_events

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
        events = self.input_manager.event_queue.release_controls()
        self.key_events = list(self.process_events(events))

    def update_states(self, time_delta: float) -> None:
        """
        Checks if a state is done or has called for a game quit.

        Parameters:
            time_delta: Amount of time passed since last frame.

        """
        self.state_manager.update(time_delta)
        if self.state_manager.current_state is None:
            self.exit = True

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
    ) -> tuple[float, int]:
        """
        Compute and print the frames per second.

        This function only prints FPS if that option has been set in the
        config. It only prints the FPS if at least one second has elapsed
        since the last time it printed them.

        Parameters:
            clock_tick: Seconds elapsed since the last ``update`` call.
            fps_timer: Number of seconds elapsed since the last time the FPS
                were printed.
            frames: Number of frames printed since the last time the FPS were
                printed.

        Returns:
            Updated values of ``fps_timer`` and ``frames``. They will be the
            same as the values passed unless the FPS are printed, in which case
            they are reset to 0.
        """
        if not self.show_fps:
            return fps_timer, frames

        fps_timer += clock_tick
        if fps_timer >= 1:
            with_fps = f"{self.caption} - {frames / fps_timer:.2f} FPS"
            pg.display.set_caption(with_fps)
            return 0, 0

        return fps_timer, frames

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
        world = self.get_state_by_name(WorldState)
        world.npcs = []
        world.npcs_off_map = []
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if sprite not in world.npcs:
                        world.npcs.append(sprite)
                    if sprite in world.npcs_off_map:
                        world.npcs_off_map.remove(sprite)

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if sprite not in world.npcs_off_map:
                        world.npcs_off_map.append(sprite)
                    if sprite in world.npcs:
                        world.npcs.remove(sprite)

    def get_map_filepath(self) -> Optional[str]:
        """
        Gets the filepath of the current map.

        Returns:
            File path of the current map, if there is one.

        """
        world = self.get_state_by_name(WorldState)
        return world.current_map.filename

    def get_map_name(self) -> str:
        """
        Gets the name of the current map.

        Returns:
            Name of the current map.

        """
        map_path = self.get_map_filepath()
        if map_path is None:
            raise ValueError("Name of the map requested when no map is active")

        # extract map name from path
        return os.path.basename(map_path)

    """
    The following methods provide an interface to the state stack
    """

    @overload
    def get_state_by_name(self, state_name: str) -> State:
        pass

    @overload
    def get_state_by_name(
        self,
        state_name: type[StateType],
    ) -> StateType:
        pass

    def get_state_by_name(
        self,
        state_name: Union[str, type[State]],
    ) -> State:
        """
        Query the state stack for a state by the name supplied.
        """
        return self.state_manager.get_state_by_name(state_name)

    def get_queued_state_by_name(
        self,
        state_name: str,
    ) -> tuple[str, Mapping[str, Any]]:
        """
        Query the state stack for a state by the name supplied.
        """
        return self.state_manager.get_queued_state_by_name(state_name)

    def queue_state(self, state_name: str, **kwargs: Any) -> None:
        """Queue a state"""
        self.state_manager.queue_state(state_name, **kwargs)

    def pop_state(self, state: Optional[State] = None) -> None:
        """Pop current state, or another"""
        self.state_manager.pop_state(state)

    def remove_state(self, state: State) -> None:
        """Remove a state"""
        self.state_manager.remove_state(state)

    def remove_state_by_name(self, state: str) -> None:
        """Remove a state by name"""
        self.state_manager.remove_state_by_name(state)

    @overload
    def push_state(self, state_name: str, **kwargs: Any) -> State:
        pass

    @overload
    def push_state(
        self,
        state_name: StateType,
        **kwargs: Any,
    ) -> StateType:
        pass

    def push_state(
        self,
        state_name: Union[str, StateType],
        **kwargs: Any,
    ) -> State:
        """Push new state, by name"""
        return self.state_manager.push_state(state_name, **kwargs)

    @overload
    def replace_state(self, state_name: str, **kwargs: Any) -> State:
        pass

    @overload
    def replace_state(
        self,
        state_name: StateType,
        **kwargs: Any,
    ) -> StateType:
        pass

    def replace_state(
        self,
        state_name: Union[str, State],
        **kwargs: Any,
    ) -> State:
        """Replace current state with new one"""
        return self.state_manager.replace_state(state_name, **kwargs)

    def push_state_with_timeout(
        self,
        state_name: Union[str, StateType],
        updates: int = 1,
    ) -> None:
        """Push new state, by name, by with timeout"""
        self.state_manager.push_state_with_timeout(state_name, updates)

    @property
    def active_states(self) -> Sequence[State]:
        """List of active states"""
        return self.state_manager.active_states

    @property
    def current_state(self) -> Optional[State]:
        """Current State object, or None"""
        return self.state_manager.current_state

    @property
    def active_state_names(self) -> Sequence[str]:
        """List of names of active states"""
        return self.state_manager.get_active_state_names()
