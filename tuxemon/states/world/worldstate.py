# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import itertools
import logging
import os
import uuid
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Optional,
    Union,
    no_type_check,
)

import pygame
from pygame.rect import Rect

from tuxemon import networking, prepare, state
from tuxemon.boundary import BoundaryChecker
from tuxemon.camera import Camera, CameraManager, project
from tuxemon.db import Direction
from tuxemon.entity import Entity
from tuxemon.graphics import ColorLike
from tuxemon.map import RegionProperties, TuxemonMap, dirs2, proj
from tuxemon.map_loader import TMXMapLoader, YAMLEventLoader
from tuxemon.map_view import MapRenderer
from tuxemon.math import Vector2
from tuxemon.movement import Pathfinder
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event
from tuxemon.session import local_session
from tuxemon.states.world.world_menus import WorldMenuState
from tuxemon.teleporter import Teleporter

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.networking import EventData
    from tuxemon.npc import NPC
    from tuxemon.player import Player

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


class WorldState(state.State):
    """The state responsible for the world game play"""

    def __init__(
        self,
        map_name: str,
    ) -> None:
        super().__init__()

        from tuxemon.player import Player

        self.boundary_checker = BoundaryChecker()
        self.teleporter = Teleporter(self)
        self.pathfinder = Pathfinder(self, self.boundary_checker)
        # Provide access to the screen surface
        self.screen = self.client.screen
        self.tile_size = prepare.TILE_SIZE

        #####################################################################
        #                           Player Details                           #
        ######################################################################

        self.npcs: list[NPC] = []
        self.npcs_off_map: list[NPC] = []
        self.wants_to_move_char: dict[str, Direction] = {}
        self.allow_char_movement: list[str] = []

        ######################################################################
        #                              Map                                   #
        ######################################################################

        self.current_map: TuxemonMap

        ######################################################################
        #                            Transitions                             #
        ######################################################################

        # default variables for transition
        self.transition_alpha = 0
        self.transition_surface: Optional[pygame.surface.Surface] = None
        self.in_transition = False

        if local_session.player is None:
            new_player = Player(prepare.PLAYER_NPC, world=self)
            local_session.player = new_player

        self.camera = Camera(local_session.player, self.boundary_checker)
        self.map_renderer = MapRenderer(self, self.screen, self.camera)
        self.camera_manager = CameraManager()
        self.camera_manager.add_camera(self.camera)

        if map_name:
            self.change_map(map_name)
        else:
            raise ValueError("You must pass the map name to load")

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.unlock_controls(self.player)

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.lock_controls(self.player)
        self.stop_char(self.player)

    def set_transition_surface(self, color: ColorLike) -> None:
        self.transition_surface = pygame.Surface(
            self.client.screen.get_size(), pygame.SRCALPHA
        )
        self.transition_surface.fill(color)

    def set_transition_state(self, in_transition: bool) -> None:
        """Update the transition state."""
        self.in_transition = in_transition

    def fade_out(self, duration: float, color: ColorLike) -> None:
        self.set_transition_surface(color)
        self.animate(
            self,
            transition_alpha=255,
            initial=0,
            duration=duration,
            round_values=True,
        )
        self.stop_char(self.player)
        self.lock_controls(self.player)

    def fade_in(self, duration: float, color: ColorLike) -> None:
        self.set_transition_surface(color)
        self.animate(
            self,
            transition_alpha=0,
            initial=255,
            duration=duration,
            round_values=True,
        )
        self.task(
            partial(self.unlock_controls, self.player),
            max(duration, 0),
        )

    def broadcast_player_teleport_change(self) -> None:
        """Tell clients/host that player has moved after teleport."""
        # Set the transition variable in event_data to false when we're done
        self.client.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        self.network = self.client.network_manager
        if self.network.isclient or self.network.ishost:
            assert self.network.client
            self.client.add_clients_to_map(self.network.client.client.registry)
            self.network.client.update_player(self.player.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.npcs:
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

        for npc in self.npcs_off_map:
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

    def update(self, time_delta: float) -> None:
        """
        The primary game loop that executes the world's functions every frame.

        Parameters:
            time_delta: Amount of time passed since last frame.

        """
        super().update(time_delta)
        self.update_npcs(time_delta)
        self.map_renderer.update(time_delta)
        self.camera_manager.update()

        logger.debug("*** Game Loop Started ***")

    def draw(self, surface: pygame.surface.Surface) -> None:
        """
        Draw the game world to the screen.

        Parameters:
            surface: Surface to draw into.

        """
        self.screen = surface
        self.map_renderer.draw(surface, self.current_map)
        self.fullscreen_animations(surface)

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

        if event.button == intentions.WORLD_MENU:
            if event.pressed:
                logger.info("Opening main menu!")
                self.client.release_controls()
                self.client.push_state(WorldMenuState())
                return None

        # map may not have a player registered
        if self.player is None:
            return None

        if event.button == intentions.INTERACT:
            if event.pressed:
                multiplayer = False
                if multiplayer:
                    self.check_interactable_space()
                    return None

        if event.button == intentions.RUN:
            if event.held:
                self.player.moverate = self.client.config.player_runrate
            else:
                self.player.moverate = self.client.config.player_walkrate

        # If we receive an arrow key press, set the facing and
        # moving direction to that direction
        direction = direction_map.get(event.button)
        if direction is not None:
            if self.camera.follows_entity:
                if event.held:
                    self.wants_to_move_char[self.player.slug] = direction
                    if self.player.slug in self.allow_char_movement:
                        self.move_char(self.player, direction)
                    return None
                elif not event.pressed:
                    if self.player.slug in self.wants_to_move_char.keys():
                        self.stop_char(self.player)
                        return None
            else:
                return self.camera_manager.handle_input(event)

        if prepare.DEV_TOOLS:
            if event.pressed and event.button == intentions.NOCLIP:
                self.player.ignore_collisions = (
                    not self.player.ignore_collisions
                )
                return None

            if event.pressed and event.button == intentions.RELOAD_MAP:
                self.current_map.reload_tiles()
                return None

        # if we made it this far, return the event for others to use
        return event

    ####################################################
    #            Pathfinding and Collisions            #
    ####################################################
    """
    Eventually refactor pathing/collisions into a more generic class
    so it doesn't rely on a running game, players, or a screen
    """

    def add_player(self, player: Player) -> None:
        """
        WIP.  Eventually handle players coming and going (for server).

        Parameters:
            player: Player to add to the world.

        """
        self.player = player
        self.add_entity(player)

    def add_entity(self, entity: Entity[Any]) -> None:
        """
        Add an entity to the world.

        Parameters:
            entity: Entity to add.

        """
        from tuxemon.npc import NPC

        entity.world = self

        # Maybe in the future the world should have a dict of entities instead?
        if isinstance(entity, NPC):
            self.npcs.append(entity)

    def get_entity(self, slug: str) -> Optional[NPC]:
        """
        Get an entity from the world.

        Parameters:
            slug: The entity slug.

        """
        return next((npc for npc in self.npcs if npc.slug == slug), None)

    def get_entity_by_iid(self, iid: uuid.UUID) -> Optional[NPC]:
        """
        Get an entity from the world.

        Parameters:
            iid: The entity instance ID.

        """
        return next((npc for npc in self.npcs if npc.instance_id == iid), None)

    def get_entity_pos(self, pos: tuple[int, int]) -> Optional[NPC]:
        """
        Get an entity from the world by its position.

        Parameters:
            pos: The entity position.

        """
        return next((npc for npc in self.npcs if npc.tile_pos == pos), None)

    def remove_entity(self, slug: str) -> None:
        """
        Remove an entity from the world.

        Parameters:
            slug: The entity slug.

        """
        npc = self.get_entity(slug)
        if npc:
            npc.remove_collision()
            self.npcs.remove(npc)

    def get_all_entities(self) -> Sequence[NPC]:
        """
        List of players and NPCs, for collision checking.

        Returns:
            The list of entities in the map.

        """
        return self.npcs

    def get_all_monsters(self) -> list[Monster]:
        """
        List of all monsters in the world.

        Returns:
            The list of monsters in the map.

        """
        return [monster for npc in self.npcs for monster in npc.monsters]

    def get_monster_by_iid(self, iid: uuid.UUID) -> Optional[Monster]:
        """
        Get a monster from the world.

        Parameters:
            iid: The monster instance ID.

        """
        return next(
            (
                monster
                for npc in self.npcs
                for monster in npc.monsters
                if monster.instance_id == iid
            ),
            None,
        )

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
        for npc in self.get_all_entities():
            collision_dict[npc.tile_pos] = self._get_region_properties(
                npc.tile_pos, npc
            )

        # Add surface map entries to the collision dictionary
        for coords, surface in self.surface_map.items():
            for label, value in surface.items():
                if float(value) == 0:
                    collision_dict[coords] = self._get_region_properties(
                        coords, label
                    )

        collision_dict.update({k: v for k, v in self.collision_map.items()})

        return dict(collision_dict)

    def _get_region_properties(
        self, coords: tuple[int, int], entity_or_label: Union[NPC, str]
    ) -> RegionProperties:
        region = self.collision_map.get(coords)
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
        self,
        start: tuple[int, int],
        dest: tuple[int, int],
    ) -> Optional[Sequence[tuple[int, int]]]:
        return self.pathfinder.pathfind(start, dest)

    def get_explicit_tile_exits(
        self,
        position: tuple[int, int],
        tile: RegionProperties,
        skip_nodes: Optional[set[tuple[int, int]]] = None,
    ) -> list[tuple[float, ...]]:
        """
        Check for exits from tile which are defined in the map.

        This will return exits which were defined by the map creator.

        Checks "endure" and "exits" properties of the tile.

        Parameters:
            position: Original position.
            tile: Region properties of the tile.
            skip_nodes: Set of nodes to skip.

        """
        skip_nodes = skip_nodes or set()
        exits: list[tuple[float, ...]] = []

        try:
            # Check if the player's current position has any exit limitations.
            if tile.endure:
                direction = (
                    self.player.facing
                    if len(tile.endure) > 1 or not tile.endure
                    else tile.endure[0]
                )
                exit_position = tuple(dirs2[direction] + position)
                if exit_position not in skip_nodes:
                    exits.append(exit_position)

            # Check if the tile explicitly defines exits.
            if tile.exit_from:
                exits.extend(
                    tuple(dirs2[direction] + position)
                    for direction in tile.exit_from
                    if tuple(dirs2[direction] + position) not in skip_nodes
                )
        except (KeyError, TypeError):
            return []

        return exits

    ####################################################
    #              Character Movement                  #
    ####################################################
    def lock_controls(self, char: NPC) -> None:
        """Prevent input from moving the character."""
        if char.slug in self.allow_char_movement:
            self.allow_char_movement.remove(char.slug)

    def unlock_controls(self, char: NPC) -> None:
        """
        Allow the character to move.

        If the character was previously holding a direction down,
        then the character will start moving after this is called.

        """
        self.allow_char_movement.append(char.slug)
        if char.slug in self.wants_to_move_char.keys():
            _dir = self.wants_to_move_char.get(char.slug, Direction.down)
            self.move_char(char, _dir)

    def stop_char(self, char: NPC) -> None:
        """
        Reset controls and stop character movement at once.
        Do not lock controls. Movement is gracefully stopped.
        If character was in a movement, then complete it before stopping.

        """
        if char.slug in self.wants_to_move_char.keys():
            del self.wants_to_move_char[char.slug]
        self.client.release_controls()
        char.cancel_movement()

    def stop_and_reset_char(self, char: NPC) -> None:
        """
        Reset controls, stop character and abort movement. Do not lock controls.

        Movement is aborted here, so the character will not complete movement
        to a tile.  It will be reset to the tile where movement started.

        Use if you don't want to trigger another tile event.

        """
        if char.slug in self.wants_to_move_char.keys():
            del self.wants_to_move_char[char.slug]
        self.client.release_controls()
        char.abort_movement()

    def move_char(self, char: NPC, direction: Direction) -> None:
        """
        Move character in a direction. Changes facing.

        Parameters:
            char: Character.
            direction: New direction of the character.

        """
        char.move_direction = direction

    def get_pos_from_tilepos(
        self,
        tile_position: Vector2,
    ) -> tuple[int, int]:
        """
        Returns the map pixel coordinate based on tile position.

        USE this to draw to the screen.

        Parameters:
            tile_position: An [x, y] tile position.

        Returns:
            The pixel coordinates to draw at the given tile position.

        """
        assert self.current_map.renderer
        cx, cy = self.current_map.renderer.get_center_offset()
        px, py = project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def update_npcs(self, time_delta: float) -> None:
        """
        Allow NPCs to be updated.

        Parameters:
            time_delta: Ellapsed time.

        """
        # TODO: This function may be moved to a server
        # Draw any game NPC's
        for entity in self.get_all_entities():
            entity.update(time_delta)

            if entity.update_location:
                char_dict = {"tile_pos": entity.final_move_dest}
                networking.update_client(entity, char_dict, self.client)
                entity.update_location = False

        # Move any multiplayer characters that are off map so we know where
        # they should be when we change maps.
        for entity in self.npcs_off_map:
            entity.update(time_delta)

    def _collision_box_to_pgrect(self, box: tuple[int, int]) -> Rect:
        """
        Returns a Rect (in screen-coords) version of a collision box (in world-coords).
        """

        # For readability
        x, y = self.get_pos_from_tilepos(Vector2(box))
        tw, th = self.tile_size

        return Rect(x, y, tw, th)

    def _npc_to_pgrect(self, npc: NPC) -> pygame.rect.Rect:
        """Returns a Rect (in screen-coords) version of an NPC's bounding box."""
        pos = self.get_pos_from_tilepos(proj(npc.position3))
        return Rect(pos, self.tile_size)

    ####################################################
    #                Debug Drawing                     #
    ####################################################
    def debug_drawing(self, surface: pygame.surface.Surface) -> None:
        from pygame.gfxdraw import box

        surface.lock()

        # draw events
        for event in self.client.events:
            vector = Vector2(event.x, event.y)
            topleft = self.get_pos_from_tilepos(vector)
            size = project((event.w, event.h))
            rect = topleft, size
            box(surface, rect, (0, 255, 0, 128))

        # We need to iterate over all collidable objects.  So, let's start
        # with the walls/collision boxes.
        box_iter = map(self._collision_box_to_pgrect, self.collision_map)

        # Next, deal with solid NPCs.
        npc_iter = map(self._npc_to_pgrect, self.npcs)

        # draw noc and wall collision tiles
        red = (255, 0, 0, 128)
        for item in itertools.chain(box_iter, npc_iter):
            box(surface, item, red)

        # draw center lines to verify camera is correct
        w, h = surface.get_size()
        cx, cy = w // 2, h // 2
        pygame.draw.line(surface, (255, 50, 50), (cx, 0), (cx, h))
        pygame.draw.line(surface, (255, 50, 50), (0, cy), (w, cy))

        surface.unlock()

    ####################################################
    #         Full Screen Animations Functions         #
    ####################################################
    def fullscreen_animations(self, surface: pygame.surface.Surface) -> None:
        """
        Handles fullscreen animations such as transitions, cutscenes, etc.

        Parameters:
            surface: Surface to draw onto.

        """
        if self.in_transition:
            assert self.transition_surface
            self.transition_surface.set_alpha(self.transition_alpha)
            surface.blit(self.transition_surface, (0, 0))

    ####################################################
    #             Map Change/Load Functions            #
    ####################################################
    def change_map(self, map_name: str) -> None:
        """
        Changes the current map and updates the player state.

        Parameters:
            map_name: The name of the map to load.
        """
        self.load_and_update_map(map_name)
        self.update_player_state()

    def load_and_update_map(self, map_name: str) -> None:
        """
        Loads a new map and updates the game state accordingly.

        This method loads the map data, updates the game state, and notifies
        the client and boundary checker. The currently loaded map is updated
        because the event engine loads event conditions and event actions from
        the currently loaded map. If we change maps, we need to update this.

        Parameters:
            map_name: The name of the map to load.
        """
        logger.debug(f"Loading map '{map_name}' from disk.")
        map_data = self.load_map_data(map_name)

        self.current_map = map_data
        self.collision_map = map_data.collision_map
        self.surface_map = map_data.surface_map
        self.collision_lines_map = map_data.collision_lines_map
        self.map_size = map_data.size
        self.map_area = map_data.area

        self.boundary_checker.update_boundaries(self.map_size)
        self.client.load_map(map_data)
        self.clear_npcs()

    def clear_npcs(self) -> None:
        """
        Clears all existing NPCs from the game state.
        """
        self.npcs = []
        self.npcs_off_map = []

    def update_player_state(self) -> None:
        """
        Updates the player's state after changing maps.

        Parameters:
            player: The player object to update.
        """
        player = local_session.player
        self.add_player(player)
        self.stop_char(player)

    def load_map_data(self, path: str) -> TuxemonMap:
        """
        Returns map data as a dictionary to be used for map changing.

        Parameters:
            path: Path of the map to load.

        Returns:
            Loaded map.

        """
        txmn_map = TMXMapLoader().load(path)
        yaml_files = [path.replace(".tmx", ".yaml")]

        if txmn_map.scenario:
            _scenario = prepare.fetch("maps", f"{txmn_map.scenario}.yaml")
            yaml_files.append(_scenario)

        _events = list(txmn_map.events)
        _inits = list(txmn_map.inits)
        events = {"event": _events, "init": _inits}

        yaml_loader = YAMLEventLoader()

        for yaml_file in yaml_files:
            if os.path.exists(yaml_file):
                yaml_data = yaml_loader.load_events(yaml_file, "event")
                events["event"].extend(yaml_data["event"])
                yaml_data = yaml_loader.load_events(yaml_file, "init")
                events["init"].extend(yaml_data["init"])
            else:
                logger.warning(f"YAML file {yaml_file} not found")

        txmn_map.events = events["event"]
        txmn_map.inits = events["init"]
        return txmn_map

    @no_type_check  # only used by multiplayer which is disabled
    def check_interactable_space(self) -> bool:
        """
        Checks to see if any Npc objects around the player are interactable.

        It then populates a menu of possible actions.

        Returns:
            ``True`` if there is an Npc to interact with. ``False`` otherwise.

        """
        collision_dict = self.player.get_collision_map(
            self
        )  # FIXME: method doesn't exist
        player_tile_pos = self.player.tile_pos
        collisions = self.player.collision_check(
            player_tile_pos, collision_dict, self.collision_lines_map
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
                    for npc in self.npcs:
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
                        pd = local_session.player.__dict__
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
