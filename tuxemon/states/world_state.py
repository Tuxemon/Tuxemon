# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Optional,
    no_type_check,
)

from pygame.surface import Surface

from tuxemon import networking, prepare
from tuxemon.camera.camera import Camera
from tuxemon.db import Direction
from tuxemon.faction.manager import FactionManager
from tuxemon.map.map_view import NullRenderer
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event
from tuxemon.save_state import WorldSave
from tuxemon.session import Session
from tuxemon.state.state import State
from tuxemon.world.input import InputRouter, WorldInputHandler
from tuxemon.world.manager import WorldMenuManager
from tuxemon.world.transition import WorldTransition

if TYPE_CHECKING:
    from tuxemon.map.map_view import AbstractRenderer
    from tuxemon.networking import EventData

logger = logging.getLogger(__name__)


class WorldState(State):
    """The state responsible for the world game play"""

    name: ClassVar[str] = "WorldState"

    def __init__(
        self,
        session: Session,
        map_name: Optional[str] = None,
        renderer: Optional[AbstractRenderer] = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.session.set_world(self)
        self.tile_size = prepare.TILE_SIZE
        self.menu_manager = WorldMenuManager(self.client)
        self.transition_manager = WorldTransition(
            self, self.client.movement_manager
        )
        self.player = self.session.player
        self.camera = Camera(self.player, self.client.boundary)
        self.client.camera_manager.add_camera(self.camera)
        self.faction_manager = FactionManager()
        self.register_input_handlers()

        if map_name:
            self.client.map_transition.change_map(map_name)
        else:
            logger.warning("No map name provided — using fallback renderer.")
            self.client.set_renderer(renderer or NullRenderer())

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

    def register_input_handlers(self) -> None:
        self.input_handler = WorldInputHandler(
            self.player, self.client, self.menu_manager
        )
        self.input_router = InputRouter()

        for button, config in self.input_handler.get_handlers().items():
            self.input_router.register(button, config)

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.client.movement_manager.unlock_controls(self.player)

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.client.movement_manager.lock_controls(self.player)
        self.client.movement_manager.stop_char(self.player)

    def broadcast_player_teleport_change(self) -> None:
        """Tell clients/host that player has moved after teleport."""
        # Set the transition variable in event_data to false when we're done
        self.client.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        self.network = self.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            current_map = self.client.get_map_name()
            self.client.npc_manager.add_clients_to_map(
                self.network.client.client.registry, current_map
            )
            self.network.client.update_player(self.player.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.client.npc_manager.npcs.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

        for npc in self.client.npc_manager.npcs_off_map.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

    def update(self, time_delta: float) -> None:
        """
        The primary game loop that executes the world's functions every frame.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        super().update(time_delta)
        self.client.npc_manager.update_npcs(time_delta, self.client)
        self.client.npc_manager.update_npcs_off_map(time_delta, self.client)
        self.client.map_renderer.update(time_delta)

        logger.debug("*** Game Loop Started ***")

    def draw(self, surface: Surface) -> None:
        """Draw the game world to the screen."""
        self.client.map_renderer.draw(
            surface, self.client.map_manager.current_map
        )
        self.transition_manager.draw(surface)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
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
        event = translate_input_event(event)
        if self.player is None:
            return None

        routed = self.input_router.route(event)
        if routed is None:
            return None

        return self.client.movement_manager.handle_directional_input(
            self.player, routed
        )

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
                    if direction == Direction.up:
                        tile = (player_tile_pos[0], player_tile_pos[1] - 1)
                    elif direction == Direction.down:
                        tile = (player_tile_pos[0], player_tile_pos[1] + 1)
                    elif direction == Direction.left:
                        tile = (player_tile_pos[0] - 1, player_tile_pos[1])
                    elif direction == Direction.right:
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
        networking.update_client(target, event_data["char_dict"], self.client)
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
                        world = self.client.current_state
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
