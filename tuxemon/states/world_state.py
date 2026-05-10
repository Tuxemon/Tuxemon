# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    no_type_check,
)

from pygame.surface import Surface

from tuxemon.camera.camera import Camera
from tuxemon.db import Direction
from tuxemon.event.eventmiddleware import (
    CameraControlMiddleware,
    DevToolsMiddleware,
    InputTranslatorMiddleware,
    MovementMiddleware,
    WorldCommandMiddleware,
)
from tuxemon.faction.manager import FactionManager
from tuxemon.platform.events import PlayerInput
from tuxemon.prepare import DEV_TOOLS
from tuxemon.save_system.save_state import WorldSave
from tuxemon.session import Session
from tuxemon.state.state import State
from tuxemon.world.manager import WorldMenuManager
from tuxemon.world.transition import WorldTransition

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.network.networking import EventData, update_client

logger = logging.getLogger(__name__)


class WorldState(State):
    """The state responsible for the world game play"""

    name: ClassVar[str] = "WorldState"

    def __init__(
        self,
        client: BaseClient,
        session: Session,
        map_name: str | None = None,
        yaml_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)
        mw = self.client.event_manager.get_middleware_instance(
            InputTranslatorMiddleware
        )
        if mw is None:
            mw = InputTranslatorMiddleware()
            self.client.event_manager.add_middleware(mw, priority=0)

        self.input_translator_mw = mw
        self.session = session
        self.session.set_world(self)
        self.tile_size = self.client.context.tile_size
        self.menu_manager = WorldMenuManager(self.client)
        self.transition_manager = WorldTransition(
            self, self.client.movement_manager, self.client.context.resolution
        )
        self.player = self.session.player
        self.camera = Camera(
            self.player, self.client.boundary, self.client.context
        )
        self.client.camera_manager.add_camera(self.player.slug, self.camera)
        self.faction_manager = FactionManager(self.client.event_bus)
        self.client.map_transition.change_map(map_name, yaml_name)
        self.client.reset_renderer()

        self.command_mw = WorldCommandMiddleware(
            self.player,
            self.client.state_manager,
            self.client.input_manager,
            self.client.event_manager,
            self.menu_manager,
        )
        self.camera_mw = CameraControlMiddleware(self.client.camera_manager)
        self.movement_mw = MovementMiddleware(
            self.player,
            self.client.movement_manager,
            self.client.camera_manager,
        )
        self.devtools_mw = DevToolsMiddleware(
            self.player,
            self.client.map_manager,
            self.client.event_manager,
            self.client.input_manager,
        )
        self.client.event_manager.add_middleware(self.camera_mw, priority=5)
        self.client.event_manager.add_middleware(self.movement_mw, priority=10)
        if DEV_TOOLS:
            self.client.event_manager.add_middleware(
                self.devtools_mw, priority=20
            )
        self.client.event_manager.add_middleware(self.command_mw, priority=30)

    def get_state(self, session: Session) -> WorldSave:
        """Returns a WorldSave model representing the current world state."""
        return WorldSave(
            factions_manager=self.faction_manager.set_state(
                self.client.npc_manager
            ),
            menu_flags=self.menu_manager.menu_flags.export(),
        )

    def set_state(self, session: Session, save_data: WorldSave) -> None:
        """Recreates the World from the provided saved data."""
        self.faction_manager.get_state(save_data.factions_manager)
        self.menu_manager.menu_flags.import_flags(save_data.menu_flags)

    def prepare_for_teleport(self) -> None:
        """
        Stops all WorldState background activity and locks player controls
        in preparation for a map change or teleport.
        """
        self.remove_animations_of(self)
        self.stop_scheduled_callbacks()
        self.client.movement_manager.stop_char(self.player)
        self.client.movement_manager.lock_controls(self.player)

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.client.event_manager.add_middleware(
            self.input_translator_mw, priority=0
        )

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.client.event_manager.remove_middleware(self.input_translator_mw)
        self.client.movement_manager.stop_char(self.player)

    def broadcast_player_teleport_change(self) -> None:
        """Tell clients/host that player has moved after teleport."""
        self.client.npc_manager.handle_player_teleport(
            self.client, self.player, self.client.network_manager
        )

    def update(self, dt: float) -> None:
        super().update(dt)
        self.faction_manager.update(dt, self.session)
        self.client.npc_manager.update_npcs(dt, self.client)
        self.client.npc_manager.update_npcs_off_map(dt, self.client)
        self.client.map_renderer.update(dt)

    def draw(self, surface: Surface) -> None:
        """Draw the game world to the screen."""
        self.client.map_renderer.draw(
            surface, self.client.map_manager.current_map
        )
        self.transition_manager.draw(surface)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        """
        Handles player input events.

        This function is only called when the player provides input such
        as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        Parameters:
            event: Event to handle.

        Returns:
            Passed events, if other states should process it, ``None``
            otherwise.
        """
        if self.player is None:
            return None
        return event

    @no_type_check  # only used by multiplayer which is disabled
    def check_interactable_space(self) -> bool:
        """
        Checks to see if any Npc objects around the player are interactable.

        It then populates a menu of possible actions.

        Returns:
            ``True`` if there is an Npc to interact with. ``False`` otherwise.
        """
        collision_dict = self.get_collision_map()
        player_tile_pos = self.player.tile_pos
        collisions = self.player.collision_check(
            player_tile_pos,
            collision_dict,
            self.client.map_manager.collision_lines_map,
        )
        if not collisions:
            pass
        else:
            for direction in collisions:
                if self.player.facing == direction:
                    if direction == Direction.UP:
                        tile = (player_tile_pos[0], player_tile_pos[1] - 1)
                    elif direction == Direction.DOWN:
                        tile = (player_tile_pos[0], player_tile_pos[1] + 1)
                    elif direction == Direction.LEFT:
                        tile = (player_tile_pos[0] - 1, player_tile_pos[1])
                    elif direction == Direction.RIGHT:
                        tile = (player_tile_pos[0] + 1, player_tile_pos[1])
                    for npc in self.client.npc_manager.npcs:
                        tile_pos = (
                            int(round(npc.tile_pos[0])),
                            int(round(npc.tile_pos[1])),
                        )
                        if tile_pos == tile:
                            logger.info("Opening interaction menu!")
                            self.client.push_state("InteractionMenu")
                            return True
                        else:
                            continue

        return False

    @no_type_check  # FIXME: dead code
    def handle_interaction(
        self, event_data: EventData, registry: Mapping[str, Any]
    ) -> None:
        """
        Presents options window when another player has interacted with this player.

        :param event_data: Information on the type of interaction and who sent it.
        :param registry:

        :type event_data: Dictionary
        :type registry: Dictionary
        """
        target = registry[event_data["target"]]["sprite"]
        target_name = str(target.name)
        update_client(target, event_data["char_dict"], self.client)
        if event_data["interaction"] == "DUEL":
            if not event_data["response"]:
                self.interaction_menu.visible = True
                self.interaction_menu.interactable = True
                self.interaction_menu.player = target
                self.interaction_menu.interaction = "DUEL"
                self.interaction_menu.menu_items = [
                    target_name + " would like to Duel!",
                    "Accept",
                    "Decline",
                ]
            else:
                if self.wants_duel:
                    if event_data["response"] == "Accept":
                        pd = self.player.__dict__
                        event_data = {
                            "type": "CLIENT_INTERACTION",
                            "interaction": "START_DUEL",
                            "target": [event_data["target"]],
                            "response": None,
                            "char_dict": {
                                "monsters": pd["monsters"],
                                "inventory": pd["inventory"],
                            },
                        }
                        self.client.server.notify_client_interaction(
                            "cuuid", event_data
                        )
