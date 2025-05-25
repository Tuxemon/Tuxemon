# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Any, Optional, TypeVar, Union, overload

import pygame
from pygame.surface import Surface

from tuxemon.audio import MusicPlayerState, SoundManager
from tuxemon.boundary import BoundaryChecker
from tuxemon.camera import CameraManager
from tuxemon.cli.processor import CommandProcessor
from tuxemon.config import TuxemonConfig
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.eventmanager import EventManager
from tuxemon.event.eventpersist import EventPersist
from tuxemon.map_loader import MapLoader
from tuxemon.map_manager import MapManager
from tuxemon.networking import NetworkManager
from tuxemon.npc_manager import NPCManager
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.input_manager import InputManager
from tuxemon.rumble import RumbleManager
from tuxemon.session import local_session
from tuxemon.state import HookManager, State, StateManager, StateRepository
from tuxemon.state_draw import EventDebugDrawer, Renderer, StateDrawer

StateType = TypeVar("StateType", bound=State)

logger = logging.getLogger(__name__)


class ClientState(Enum):
    RUNNING = "running"
    EXITING = "exiting"
    DONE = "done"


class LocalPygameClient:
    """
    Client class for the entire project.

    Contains the game loop and the event_loop, which passes events to
    States as needed.

    Parameters:
        config: The configuration for the game.
        screen: The surface where the game is rendered.
    """

    def __init__(self, config: TuxemonConfig, screen: Surface) -> None:
        self.config = config

        self.hook_manager = HookManager()
        self.state_repository = StateRepository()
        self.state_manager = StateManager(
            package="tuxemon.states",
            hook=self.hook_manager,
            repository=self.state_repository,
            on_state_change=self.on_state_change,
        )
        self.state_manager.auto_state_discovery()
        self.screen = screen
        self.state = ClientState.RUNNING
        self.caption = config.window_caption
        self.fps = config.fps
        self.show_fps = config.show_fps
        self.current_time = 0.0

        # setup controls
        self.input_manager = InputManager(config)

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Initialize drawers
        self.state_drawer = StateDrawer(
            self.screen, self.state_manager, config
        )
        self.event_debug_drawer = EventDebugDrawer(self.screen)
        self.renderer = Renderer(
            self.screen,
            self.state_drawer,
            config.window_caption,
        )

        # Set up our networking for multiplayer.
        self.network_manager = NetworkManager(self)
        self.network_manager.initialize()

        # Set up our combat engine and router.
        # self.combat_engine = CombatEngine(self)
        # self.combat_router = CombatRouter(self, self.combat_engine)

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_manager = EventManager(self.state_manager)
        self.action_manager = ActionManager()
        self.condition_manager = ConditionManager()
        self.event_engine = EventEngine(
            local_session, self.action_manager, self.condition_manager
        )
        self.event_persist = EventPersist()

        self.npc_manager = NPCManager()
        self.map_loader = MapLoader()
        self.map_manager = MapManager()
        self.boundary = BoundaryChecker()
        self.camera_manager = CameraManager()

        # Set up a variable that will keep track of currently playing music.
        self.current_music = MusicPlayerState()
        self.sound_manager = SoundManager()

        if self.config.cli:
            # TODO: There is no protection for the main thread from the cli
            # actions that execute in this thread may have undefined
            # behavior for the game.  at some point, a lock should be
            # implemented so that actions executed here have exclusive
            # control of the game loop and state.
            self.cli = CommandProcessor(self)
            thread = Thread(target=self.cli.run)
            thread.daemon = True
            thread.start()

        # Set up rumble support for gamepads
        self.rumble_manager = RumbleManager()
        self.rumble = self.rumble_manager.rumbler

        # TODO: phase these out
        self.key_events: Sequence[PlayerInput] = []
        self.event_data: dict[str, Any] = {}

    @property
    def is_running(self) -> bool:
        return self.state == ClientState.RUNNING

    def on_state_change(self) -> None:
        logger.debug("State change detected. Resetting controls.")
        self.event_manager.release_controls(self.input_manager)

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
        flip = pygame.display.update
        clock = time.time
        frame_length = 1.0 / self.fps
        time_since_draw = 0.0
        last_update = clock()

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                clock_tick = clock() - last_update
                last_update = clock()
                time_since_draw += clock_tick
                update(clock_tick)
                if time_since_draw >= frame_length:
                    time_since_draw -= frame_length
                    draw()
                    if self.input_manager.controller_overlay:
                        self.input_manager.controller_overlay.draw(screen)
                    flip()
                if self.config.show_fps:
                    self.renderer.update_fps(clock_tick)
                time.sleep(0.01)
            elif self.state == ClientState.EXITING:
                self.perform_cleanup()
                self.state = ClientState.DONE

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
        self.key_events = list(self.event_manager.process_events(events))

        # Run our event engine which will check to see if game conditions
        # are met and run an action associated with that condition.
        self.event_data = {}

        self.event_engine.update(time_delta)

        if self.event_data:
            logger.debug("Event Data:" + str(self.event_data))

        # Update the game engine
        self.update_states(time_delta)

    def quit(self) -> None:
        """Handles quitting the game."""
        self.state = ClientState.EXITING

    def perform_cleanup(self) -> None:
        """Handles necessary cleanup before shutting down."""
        self.current_music.stop()
        logger.info("Performing cleanup before exiting...")

    def update_states(self, time_delta: float) -> None:
        """
        Checks if a state is done or has called for a game quit.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        self.state_manager.update(time_delta)
        if self.state_manager.current_state is None:
            self.state = ClientState.EXITING

    def draw(self) -> None:
        """Centralized draw logic."""
        self.renderer.draw(
            frame_number=self.frame_number,
            save_to_disk=self.save_to_disk,
            collision_map=self.config.collision_map,
            debug_drawer=self.event_debug_drawer,
            partial_events=self.event_engine.partial_events,
        )
        self.frame_number += 1

    def get_map_name(self) -> str:
        """
        Gets the name of the current map.

        Returns:
            Name of the current map.
        """
        map_path = self.map_manager.get_map_filepath()
        if map_path is None:
            raise ValueError("Name of the map requested when no map is active")
        return Path(map_path).name

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
