# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Optional,
    Union,
    no_type_check,
)

from pygame.surface import Surface

from tuxemon import networking, prepare
from tuxemon.camera import Camera
from tuxemon.db import Direction
from tuxemon.map import RegionProperties
from tuxemon.map_view import MapRenderer
from tuxemon.movement import MovementManager, Pathfinder
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event
from tuxemon.player import Player
from tuxemon.session import Session
from tuxemon.state import State
from tuxemon.states.world.world_transition import WorldTransition
from tuxemon.teleporter import Teleporter

if TYPE_CHECKING:
    from tuxemon.entity import Entity
    from tuxemon.networking import EventData
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

direction_map: Mapping[int, Direction] = {
    intentions.UP: Direction.up,
    intentions.DOWN: Direction.down,
    intentions.LEFT: Direction.left,
    intentions.RIGHT: Direction.right,
}


CollisionDict = dict[
    tuple[int, int],
    Optional[RegionProperties],
]

CollisionMap = Mapping[
    tuple[int, int],
    Optional[RegionProperties],
]


class WorldState(State):
    """The state responsible for the world game play"""

    def __init__(self, session: Session, map_name: str) -> None:
        super().__init__()
        self.session = session
        self.movement = MovementManager(self.client)
        self.teleporter = Teleporter(self.client, self)
        self.pathfinder = Pathfinder(self.client, self)
        # Provide access to the screen surface
        self.screen = self.client.screen
        self.tile_size = prepare.TILE_SIZE

        self.transition_manager = WorldTransition(self)

        self.player = Player.create(self.session, self)

        self.camera = Camera(self.player, self.client.boundary)
        self.client.camera_manager.add_camera(self.camera)
        self.map_renderer = MapRenderer(self.client)

        if map_name:
            self.change_map(map_name)
        else:
            raise ValueError("You must pass the map name to load")

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.movement.unlock_controls(self.player)

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.movement.lock_controls(self.player)
        self.movement.stop_char(self.player)

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
        self.map_renderer.update(time_delta)

        logger.debug("*** Game Loop Started ***")

    def draw(self, surface: Surface) -> None:
        """
        Draw the game world to the screen.

        Parameters:
            surface: Surface to draw into.

        """
        self.screen = surface
        if self.client.map_manager.current_map is None:
            raise ValueError("Unable to draw the game world.")
        self.map_renderer.draw(surface, self.client.map_manager.current_map)
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

        # Handle menu activation
        if event.button == intentions.WORLD_MENU and event.pressed:
            logger.info("Opening main menu!")
            self.client.event_manager.release_controls(
                self.client.input_manager
            )
            self.client.push_state("WorldMenuState", character=self.player)
            return None

        # Return early if no player is registered
        if self.player is None:
            return None

        # Handle interaction event
        if event.button == intentions.INTERACT and event.pressed:
            if False:  # Multiplayer logic placeholder
                self.check_interactable_space()
                return None

        # Handle running movement toggle
        if event.button == intentions.RUN:
            if event.held:
                self.player.mover.running()
            else:
                self.player.mover.walking()

        # Handle directional movement
        if (direction := direction_map.get(event.button)) is not None:
            if not self.camera.follows_entity:
                return self.client.camera_manager.handle_input(event)
            if event.held:
                self.movement.queue_movement(self.player.slug, direction)
                if self.movement.is_movement_allowed(self.player):
                    self.movement.move_char(self.player, direction)
                return None
            if not event.pressed and self.movement.has_pending_movement(
                self.player
            ):
                self.movement.stop_char(self.player)
                return None

        # Debug tools (DEV_TOOLS)
        if prepare.DEV_TOOLS and event.pressed:
            if event.button == intentions.NOCLIP:
                self.player.ignore_collisions = (
                    not self.player.ignore_collisions
                )
                return None
            elif event.button == intentions.RELOAD_MAP:
                assert self.client.map_manager.current_map
                self.client.map_manager.current_map.reload_tiles()
                return None

        # Return event for others to process
        return event

    ####################################################
    #            Pathfinding and Collisions            #
    ####################################################

    def get_all_tile_properties(
        self,
        surface_map: MutableMapping[tuple[int, int], dict[str, float]],
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Retrieves the coordinates of all tiles with a specific property.

        Parameters:
            map: The surface map.
            label: The label (SurfaceKeys).

        Returns:
            A list of coordinates (tuples) of tiles with the specified label.

        """
        return [
            coords for coords, props in surface_map.items() if label in props
        ]

    def update_tile_property(self, label: str, moverate: float) -> None:
        """
        Updates the movement rate property for existing tile entries in the
        surface map.

        This method modifies the moverate value for tiles that already contain
        the specified label, ensuring that no new dictionary entries are created.
        If the label is not present in a tile's properties, the tile remains
        unchanged. The update process runs efficiently to prevent unnecessary
        modifications.

        Parameters:
            label: The property key to update (e.g., terrain type).
            moverate: The new movement rate value to assign.
        """
        if label not in prepare.SURFACE_KEYS:
            return

        for coord in self.get_all_tile_properties(
            self.client.map_manager.surface_map, label
        ):
            props = self.client.map_manager.surface_map.get(coord)
            if props and props.get(label) != moverate:
                props[label] = moverate

    def all_tiles_modified(self, label: str, moverate: float) -> bool:
        """
        Checks if all tiles with the specified label have been modified.

        Parameters:
            label: The property key to check.
            moverate: The expected movement rate.

        Returns:
            True if all tiles have the expected moverate, False otherwise.
        """
        return all(
            self.client.map_manager.surface_map[coord].get(label) == moverate
            for coord in self.get_all_tile_properties(
                self.client.map_manager.surface_map, label
            )
        )

    def check_collision_zones(
        self,
        collision_map: MutableMapping[
            tuple[int, int], Optional[RegionProperties]
        ],
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Returns coordinates of specific collision zones.

        Parameters:
            collision_map: The collision map.
            label: The label to filter collision zones by.

        Returns:
            A list of coordinates of collision zones with the specific label.

        """
        return [
            coords
            for coords, props in collision_map.items()
            if props and props.key == label
        ]

    def add_collision(
        self,
        entity: Entity[Any],
        pos: Sequence[float],
    ) -> None:
        """
        Registers the given entity's position within the collision zone.

        Parameters:
            entity: The entity object to be added to the collision zone.
            pos: The X, Y coordinates (as floats) indicating the entity's position.
        """
        coords = (int(pos[0]), int(pos[1]))
        region = self.client.map_manager.collision_map.get(coords)

        enter_from = region.enter_from if entity.isplayer and region else []
        exit_from = region.exit_from if entity.isplayer and region else []
        endure = region.endure if entity.isplayer and region else []
        key = region.key if entity.isplayer and region else None

        prop = RegionProperties(
            enter_from=enter_from,
            exit_from=exit_from,
            endure=endure,
            entity=entity,
            key=key,
        )

        self.client.map_manager.collision_map[coords] = prop

    def remove_collision(self, tile_pos: tuple[int, int]) -> None:
        """
        Removes the specified tile position from the collision zone.

        Parameters:
            tile_pos: The X, Y tile coordinates to be removed from the collision map.
        """
        region = self.client.map_manager.collision_map.get(tile_pos)
        if not region:
            return  # Nothing to remove

        if any([region.enter_from, region.exit_from, region.endure]):
            prop = RegionProperties(
                region.enter_from,
                region.exit_from,
                region.endure,
                None,
                region.key,
            )
            self.client.map_manager.collision_map[tile_pos] = prop
        else:
            # Remove region
            del self.client.map_manager.collision_map[tile_pos]

    def add_collision_label(self, label: str) -> None:
        coords = self.check_collision_zones(
            self.client.map_manager.collision_map, label
        )
        properties = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[],
            key=label,
            entity=None,
        )
        if coords:
            for coord in coords:
                self.client.map_manager.collision_map[coord] = properties

    def add_collision_position(
        self, label: str, position: tuple[int, int]
    ) -> None:
        properties = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[],
            key=label,
            entity=None,
        )
        self.client.map_manager.collision_map[position] = properties

    def remove_collision_label(self, label: str) -> None:
        properties = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            key=label,
            entity=None,
        )
        coords = self.check_collision_zones(
            self.client.map_manager.collision_map, label
        )
        if coords:
            for coord in coords:
                self.client.map_manager.collision_map[coord] = properties

    def get_collision_map(self) -> CollisionMap:
        """
        Return dictionary for collision testing.

        Returns a dictionary where keys are (x, y) tile tuples
        and the values are tiles or NPCs.

        # NOTE:
        This will not respect map changes to collisions
        after the map has been loaded!

        Returns:
            A dictionary of collision tiles.

        """
        collision_dict: DefaultDict[
            tuple[int, int], Optional[RegionProperties]
        ] = defaultdict(lambda: RegionProperties([], [], [], None, None))

        # Get all the NPCs' tile positions
        for npc in self.client.npc_manager.get_all_entities():
            collision_dict[npc.tile_pos] = self._get_region_properties(
                npc.tile_pos, npc
            )

        # Add surface map entries to the collision dictionary
        for coords, surface in self.client.map_manager.surface_map.items():
            for label, value in surface.items():
                if float(value) == 0:
                    collision_dict[coords] = self._get_region_properties(
                        coords, label
                    )

        collision_dict.update(
            {k: v for k, v in self.client.map_manager.collision_map.items()}
        )

        return dict(collision_dict)

    def _get_region_properties(
        self, coords: tuple[int, int], entity_or_label: Union[NPC, str]
    ) -> RegionProperties:
        region = self.client.map_manager.collision_map.get(coords)
        if region:
            if isinstance(entity_or_label, str):
                return RegionProperties(
                    region.enter_from,
                    region.exit_from,
                    region.endure,
                    None,
                    entity_or_label,
                )
            else:
                return RegionProperties(
                    region.enter_from,
                    region.exit_from,
                    region.endure,
                    entity_or_label,
                    region.key,
                )
        else:
            if isinstance(entity_or_label, str):
                return RegionProperties([], [], [], None, entity_or_label)
            else:
                return RegionProperties([], [], [], entity_or_label, None)

    def pathfind(
        self, start: tuple[int, int], dest: tuple[int, int], facing: Direction
    ) -> Optional[Sequence[tuple[int, int]]]:
        return self.pathfinder.pathfind(start, dest, facing)

    ####################################################
    #             Map Change/Load Functions            #
    ####################################################
    def change_map(self, map_name: str) -> None:
        """
        Changes the current map and updates the game state accordingly.

        This method loads the map data, updates the game state, and notifies
        the client and boundary checker. The currently loaded map is updated
        because the event engine loads event conditions and event actions from
        the currently loaded map. If we change maps, we need to update this.

        Parameters:
            map_name: The name of the map to load.
        """
        logger.debug(f"Loading map '{map_name}' using Client's MapLoader.")
        map_data = self.client.map_loader.load_map_data(map_name)

        self.client.event_engine.reset()
        self.client.event_engine.set_current_map(map_data)

        self.client.map_manager.load_map(map_data)
        self.client.npc_manager.clear_npcs()
        map_size = self.client.map_manager.map_size
        self.client.boundary.update_boundaries(map_size)

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
