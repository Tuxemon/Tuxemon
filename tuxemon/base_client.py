# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from enum import Enum
from queue import Empty, Queue
from threading import Thread
from typing import TYPE_CHECKING, Any, TypeVar, overload
from uuid import UUID

from tuxemon.audio import MusicPlayerState, SoundManager
from tuxemon.boundary import BoundaryChecker
from tuxemon.camera.camera import CameraManager
from tuxemon.cli.processor import CommandProcessor
from tuxemon.combat.session import CombatSession
from tuxemon.constants import paths
from tuxemon.core.active_effect import ActiveEffectManager
from tuxemon.core.asset import init_assets
from tuxemon.economy.shop_manager import ShopManager
from tuxemon.encounter import EncounterManager
from tuxemon.environment import EnvironmentManager
from tuxemon.event import get_event_bus
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventbehavior import BehaviorManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.eventmanager import EventManager
from tuxemon.event.eventpersist import EventPersist
from tuxemon.event.running import ConditionEvaluator
from tuxemon.map.collision_manager import CollisionManager
from tuxemon.map.loader import MapLoader
from tuxemon.map.manager import MapManager
from tuxemon.map.terrain import TerrainManager
from tuxemon.map.transition import MapTransition
from tuxemon.map.view import AbstractRenderer, NullRenderer
from tuxemon.menu.alert import AlertManager
from tuxemon.movement import MovementManager, Pathfinder
from tuxemon.network.manager import NetworkManager
from tuxemon.npc_manager import NPCManager
from tuxemon.park_tracker import ParkSession
from tuxemon.platform.afk_manager import AFKManager
from tuxemon.platform.input_manager import InputManager
from tuxemon.platform.input_recorder import InputRecorder
from tuxemon.platform.tools import ScriptInputCache
from tuxemon.rumble import RumbleManager
from tuxemon.session import local_session
from tuxemon.state.loader import StateLoader
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository
from tuxemon.state.state import State
from tuxemon.teleporter import Teleporter
from tuxemon.trade_manager import TradeManager
from tuxemon.world.weather import WorldWeatherManager

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.platform.events import PlayerInput
    from tuxemon.prepare import DisplayContext
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

    def __init__(self, config: TuxemonConfig, context: DisplayContext) -> None:
        init_assets()
        self.config = config
        self.context = context
        self.screen = context.screen
        self.active_effect_manager = ActiveEffectManager()

        self.event_bus = get_event_bus()
        self.state_repository = StateRepository.from_loader(
            StateLoader("tuxemon.states", paths.LIBDIR)
        )
        self.state_manager = StateManager(
            package="tuxemon.states",
            client=self,
            repository=self.state_repository,
            on_state_change=self.on_state_change,
        )
        self.state = ClientState.RUNNING
        self.current_time = 0.0

        # setup controls
        self.input_recorder = InputRecorder()
        self.afk_manager = AFKManager()
        self.input_cache = ScriptInputCache(self.event_bus)
        self.input_manager = InputManager(
            config,
            self.afk_manager,
            self.input_recorder,
            self.context.resolution,
        )

        # Set up our networking for multiplayer.
        self.network_manager = NetworkManager(self)
        self.network_manager.initialize()

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_manager = EventManager(self.event_bus, self.state_manager)
        self.action_manager = ActionManager()
        self.condition_manager = ConditionManager()
        self.evaluator = ConditionEvaluator(
            local_session, self.condition_manager
        )
        self.behavior_manager = BehaviorManager()
        self.event_engine = EventEngine(
            local_session,
            self.action_manager,
            self.evaluator,
            self.behavior_manager,
        )
        self.event_persist = EventPersist()

        self.npc_manager = NPCManager()
        self.map_loader = MapLoader(self.context)
        self.map_manager = MapManager()
        self.boundary = BoundaryChecker()
        self.camera_manager = CameraManager()

        # Set up a variable that will keep track of currently playing music.
        self.current_music = MusicPlayerState()
        self.sound_manager = SoundManager()

        # Set up rumble support for gamepads
        self.rumble_manager = RumbleManager()

        # TODO: phase these out
        self.key_events: Sequence[PlayerInput] = []
        self.event_data: dict[str, Any] = {}

        # Set up our combat engine and router.
        self.combat_session = CombatSession()
        # self.combat_engine = CombatEngine(self, self.combat_session)
        # self.combat_router = CombatRouter(self, self.combat_engine)

        self.movement_manager = MovementManager(
            self.event_manager, self.input_manager
        )
        self.terrain_manager = TerrainManager(self.map_manager)
        self.collision_manager = CollisionManager(self.map_manager)
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
            self.map_transition,
            self.npc_manager,
            self.state_manager,
        )
        self._map_renderer: AbstractRenderer = NullRenderer()

        # Various Sessions
        self.trade_manager = TradeManager(self.npc_manager)
        self.environment_manager = EnvironmentManager(self.context)
        self.encounter_manager = EncounterManager()
        self.park_session = ParkSession()
        self.weather_manager = WorldWeatherManager()
        self.cipher_processor: CipherProcessor | None = None
        self.alert_manager = AlertManager(self.event_bus)
        self.shop_manager = ShopManager()

        self.command_queue: Queue[Callable[[], None]] = Queue()

        if self.config.cli:
            local_session.set_client(self)
            self.cli = CommandProcessor(local_session)
            thread = Thread(target=self.cli.run)
            thread.daemon = True
            thread.start()

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
        self.event_bus.reset_all_events()
        local_session.reset()
        local_session.reset_time()
        logger.info("Performing cleanup before exiting...")

    def update_states(self, time_delta: float) -> None:
        """
        Checks if a state is done or has called for a game quit.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        self.network_manager.update(time_delta)
        self.input_cache.clear_frame_state()
        events = self.input_manager.process_events()

        while True:
            try:
                command = self.command_queue.get_nowait()
            except Empty:
                break
            command()
            self.command_queue.task_done()
            logger.debug("Executed queued command.")

        self.input_manager.update(time_delta)
        self.key_events = list(self.event_manager.process_events(events))

        self.event_data = {}
        self.event_engine.update(time_delta)

        if self.event_data:
            logger.debug(f"Event Data: {str(self.event_data)}")

        self.alert_manager.update(time_delta)
        self.environment_manager.update(time_delta)
        self.weather_manager.update(time_delta)
        self.state_manager.update(time_delta)
        self.rumble_manager.update(time_delta)

        if self.state_manager.current_state is None:
            self.state = ClientState.EXITING

        self.active_effect_manager.update(local_session, time_delta)

    def get_map_name(self) -> str:
        """Gets the name of the current map."""
        return self.map_manager.get_map_name()

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
    def update(self, dt: float) -> None:
        """
        Main loop for entire game.

        Must be implemented by subclasses to define how the game state is updated.

        Parameters:
            time_delta: Elapsed time since last frame.
        """

    @abstractmethod
    def queue_command(self, command: Callable[[], None]) -> None:
        """
        Queues a callable command (a function to be run) to be executed
        safely in the main thread during the next update cycle.

        Parameters:
            command: A function with no arguments that performs the desired action.
        """

    def reset_renderer(self) -> None:
        """Optional override for clients that support rendering."""

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
        state_name: str | type[State],
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

    def has_queued_state(self, state_name: str) -> bool:
        return any(
            s.name == state_name
            for s in self.state_manager.state_queue.queued_states
        )

    def queue_state(self, state_name: str, **kwargs: Any) -> None:
        """Queue a state"""
        self.state_manager.queue_state(state_name, **kwargs)

    def pop_state(self, state: State | None = None) -> None:
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
        state_name: str | StateType,
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
        state_name: str | State,
        **kwargs: Any,
    ) -> State:
        """Replace current state with new one"""
        return self.state_manager.replace_state(state_name, **kwargs)

    def push_state_with_timeout(
        self,
        state_name: str | StateType,
        updates: int = 1,
    ) -> None:
        """Push new state, by name, by with timeout"""
        self.state_manager.push_state_with_timeout(state_name, updates)

    def is_in_base_map_state(self, base_count: int | None = None) -> bool:
        return self.state_manager.is_in_base_map_state(base_count)

    def has_extra_states(self, base_count: int | None = None) -> bool:
        return self.state_manager.has_extra_states(base_count)

    @property
    def active_states(self) -> Sequence[State]:
        """List of active states"""
        return self.state_manager.active_states

    @property
    def current_state(self) -> State | None:
        """Current State object, or None"""
        return self.state_manager.current_state

    @property
    def active_state_names(self) -> Sequence[str]:
        """List of names of active states"""
        return self.state_manager.get_active_state_names()

    def get_monster_by_iid(self, iid: UUID) -> Monster | None:
        """Gets a monster object by iid among all the entities."""
        return self.npc_manager.get_monster_by_iid(iid)

    def get_monster_owner(self, monster: Monster) -> NPC | None:
        """Finds the NPC that currently owns the given monster."""
        return self.npc_manager.get_monster_owner(monster)

    def get_npc_pos(self, pos: tuple[int, int]) -> NPC | None:
        """Gets an NPC object by location (x,y)."""
        if local_session.has_player():
            player = local_session.player
            if player.tile_pos == pos:
                return player
        return self.npc_manager.get_entity_pos(pos)

    def get_npc(self, slug: str) -> NPC | None:
        """Gets an NPC object by slug."""
        if slug == "player":
            return local_session.player if local_session.has_player() else None
        return self.npc_manager.get_npc(slug)
