# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from enum import Enum
from os.path import basename
from typing import Any, Optional, TypeVar, Union, overload

from tuxemon.audio import MusicPlayerState, SoundManager
from tuxemon.boundary import BoundaryChecker
from tuxemon.config import TuxemonConfig
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.eventmanager import EventManager
from tuxemon.event.eventpersist import EventPersist
from tuxemon.map_loader import MapLoader
from tuxemon.map_manager import MapManager
from tuxemon.npc_manager import NPCManager
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.input_manager import InputManager
from tuxemon.rumble import RumbleManager
from tuxemon.session import local_session
from tuxemon.state import State, StateManager

StateType = TypeVar("StateType", bound=State)

logger = logging.getLogger(__name__)


class ClientState(Enum):
    RUNNING = "running"
    EXITING = "exiting"
    DONE = "done"


class HeadlessClient:
    """
    Headless client for server-side processing of game logic.
    This client runs without graphics, only handling events and
    game state updates.

    Parameters:
        config: The configuration for the game.
    """

    def __init__(self, config: TuxemonConfig) -> None:
        self.config = config

        self.state_manager = StateManager(
            "tuxemon.states",
            on_state_change=self.on_state_change,
        )
        self.state_manager.auto_state_discovery()
        self.state = ClientState.RUNNING
        self.show_fps = config.show_fps
        self.current_time = 0.0

        # setup controls
        self.input_manager = InputManager(config)

        # Set up our networking for multiplayer.
        # self.network_manager = NetworkManager(self)
        # self.network_manager.initialize()

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

        # Set up a variable that will keep track of currently playing music.
        self.current_music = MusicPlayerState()
        self.sound_manager = SoundManager()

        # if self.config.cli:
        #    self.cli = CommandProcessor(self)
        #    thread = Thread(target=self.cli.run)
        #    thread.daemon = True
        #    thread.start()

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
        clock = time.time
        time_since_draw = 0.0
        last_update = clock()

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                clock_tick = clock() - last_update
                last_update = clock()
                time_since_draw += clock_tick
                update(clock_tick)
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
        and update the game state.

        Parameters:
            time_delta: Elapsed time since last frame.
        """
        # Update our networking
        # self.network_manager.update(time_delta)

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

    def get_map_name(self) -> str:
        """
        Gets the name of the current map.

        Returns:
            Name of the current map.
        """
        map_path = self.map_manager.get_map_filepath()
        if map_path is None:
            raise ValueError("Name of the map requested when no map is active")

        # extract map name from path
        return basename(map_path)

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
