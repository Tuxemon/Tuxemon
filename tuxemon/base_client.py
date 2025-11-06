# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union, overload

from tuxemon.audio import MusicPlayerState, SoundManager
from tuxemon.boundary import BoundaryChecker
from tuxemon.camera.camera import CameraManager
from tuxemon.combat.session import CombatSession
from tuxemon.constants import paths
from tuxemon.event import get_event_bus
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.eventmanager import EventManager
from tuxemon.event.eventpersist import EventPersist
from tuxemon.event.running import ConditionEvaluator
from tuxemon.map.collision_manager import CollisionManager
from tuxemon.map.map_loader import MapLoader
from tuxemon.map.map_manager import MapManager
from tuxemon.map.map_transition import MapTransition
from tuxemon.map.map_view import AbstractRenderer, NullRenderer
from tuxemon.movement import MovementManager, Pathfinder
from tuxemon.networking import NetworkManager
from tuxemon.npc_manager import NPCManager
from tuxemon.park_tracker import ParkSession
from tuxemon.platform.input_manager import InputManager
from tuxemon.rumble import RumbleManager
from tuxemon.session import local_session
from tuxemon.state.loader import StateLoader
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository
from tuxemon.state.state import State
from tuxemon.teleporter import Teleporter
from tuxemon.world.weather import WorldWeatherManager

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.events import PlayerInput
    from tuxemon.state.queue import QueuedState
    from tuxemon.ui.cipher_processor import CipherProcessor

StateType = TypeVar("StateType", bound=State)

logger = logging.getLogger(__name__)


class ClientState(Enum):
    RUNNING = "running"
    EXITING = "exiting"
    DONE = "done"


class BaseClient(ABC):
    """
    Abstract base class for Tuxemon clients.

    Handles shared setup and lifecycle management for both graphical and headless clients.
    """

    def __init__(self, config: TuxemonConfig) -> None:
        self.config = config

        self.event_bus = get_event_bus()
        self.state_repository = StateRepository()
        loader = StateLoader(
            base_package="tuxemon.states", lib_dir=paths.LIBDIR
        )
        loader.auto_state_discovery(self.state_repository)
        self.state_manager = StateManager(
            package="tuxemon.states",
            event=self.event_bus,
            repository=self.state_repository,
            on_state_change=self.on_state_change,
        )
        self.state = ClientState.RUNNING
        self.current_time = 0.0

        # setup controls
        self.input_manager = InputManager(config)

        # Set up our networking for multiplayer.
        self.network_manager = NetworkManager(self)
        self.network_manager.initialize()

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_manager = EventManager(self.state_manager)
        self.action_manager = ActionManager()
        self.condition_manager = ConditionManager()
        self.evaluator = ConditionEvaluator(
            local_session, self.condition_manager
        )
        self.event_engine = EventEngine(
            local_session, self.action_manager, self.evaluator
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

        # Set up rumble support for gamepads
        self.rumble_manager = RumbleManager()
        self.rumble = self.rumble_manager.rumbler

        # TODO: phase these out
        self.key_events: Sequence[PlayerInput] = []
        self.event_data: dict[str, Any] = {}

        # Set up our combat engine and router.
        self.combat_session = CombatSession()
        # self.combat_engine = CombatEngine(self, self.combat_session)
        # self.combat_router = CombatRouter(self, self.combat_engine)

        self.movement_manager = MovementManager(
            self.event_manager, self.input_manager, self.camera_manager
        )
        self.collision_manager = CollisionManager(
            self.map_manager, self.npc_manager
        )
        self.pathfinder = Pathfinder(
            self.npc_manager,
            self.map_manager,
            self.collision_manager,
            self.boundary,
        )
        self.map_transition = MapTransition(
            self.map_loader,
            self.npc_manager,
            self.map_manager,
            self.boundary,
            self.event_engine,
        )
        self.teleporter = Teleporter(
            self.boundary,
            self.map_manager,
            self.map_transition,
            self.movement_manager,
            self.npc_manager,
            self.state_manager,
        )
        self._map_renderer: AbstractRenderer = NullRenderer()

        # Various Sessions
        self.park_session = ParkSession()
        self.weather_manager = WorldWeatherManager()
        self.cipher_processor: Optional[CipherProcessor] = None

    @property
    def is_running(self) -> bool:
        return self.state == ClientState.RUNNING

    @property
    def map_renderer(self) -> AbstractRenderer:
        return self._map_renderer

    def on_state_change(self) -> None:
        logger.debug("State change detected. Resetting controls.")
        self.event_manager.release_controls(self.input_manager)

    def quit(self) -> None:
        """Handles quitting the game."""
        self.state = ClientState.EXITING

    def perform_cleanup(self) -> None:
        """Handles necessary cleanup before shutting down."""
        self.map_loader.clear_cache()
        self.current_music.stop()
        local_session.reset()
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
        return Path(map_path).name

    def set_renderer(self, renderer: AbstractRenderer) -> None:
        """Assigns a custom renderer to the client."""
        self._map_renderer = renderer

    @abstractmethod
    def main(self) -> None:
        """
        Initiates the main game loop.

        Must be implemented by subclasses to define how the game loop is executed.
        """

    @abstractmethod
    def update(self, time_delta: float) -> None:
        """
        Main loop for entire game.

        Must be implemented by subclasses to define how the game state is updated.

        Parameters:
            time_delta: Elapsed time since last frame.
        """

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

    def get_queued_state_by_name(self, state_name: str) -> QueuedState:
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
