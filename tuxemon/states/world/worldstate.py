# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    NamedTuple,
    Optional,
    TypedDict,
    Union,
    no_type_check,
)

import pygame
from pygame.rect import Rect

from tuxemon import networking, prepare, state
from tuxemon.camera import Camera, project
from tuxemon.db import Direction
from tuxemon.entity import Entity
from tuxemon.graphics import ColorLike
from tuxemon.map import (
    PathfindNode,
    RegionProperties,
    TuxemonMap,
    dirs2,
    get_adjacent_position,
    pairs,
    proj,
)
from tuxemon.map_loader import TMXMapLoader, YAMLEventLoader
from tuxemon.math import Vector2
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.states.world.world_classes import BoundaryChecker
from tuxemon.states.world.world_menus import WorldMenuState
from tuxemon.surfanim import SurfaceAnimation
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

SpriteMap = Union[
    Mapping[str, pygame.surface.Surface],
    Mapping[str, SurfaceAnimation],
]

animation_mapping = {
    "walking": {
        "up": "back_walk",
        "down": "front_walk",
        "left": "left_walk",
        "right": "right_walk",
    },
    "idle": {"up": "back", "down": "front", "left": "left", "right": "right"},
}


class WorldSurfaces(NamedTuple):
    surface: pygame.surface.Surface
    position3: Vector2
    layer: int


class AnimationInfo(TypedDict):
    animation: SurfaceAnimation
    position: tuple[int, int]
    layer: int


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

    keymap = {
        buttons.UP: intentions.UP,
        buttons.DOWN: intentions.DOWN,
        buttons.LEFT: intentions.LEFT,
        buttons.RIGHT: intentions.RIGHT,
        buttons.A: intentions.INTERACT,
        buttons.B: intentions.RUN,
        buttons.START: intentions.WORLD_MENU,
        buttons.BACK: intentions.WORLD_MENU,
    }

    def __init__(
        self,
        map_name: str,
    ) -> None:
        super().__init__()

        from tuxemon.player import Player

        self.boundary_checker = BoundaryChecker()
        self.teleporter = Teleporter()
        # Provide access to the screen surface
        self.screen = self.client.screen
        self.screen_rect = self.screen.get_rect()
        self.resolution = prepare.SCREEN_SIZE
        self.tile_size = prepare.TILE_SIZE
        # default variables for layer
        self.layer = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.layer_color: ColorLike = prepare.TRANSPARENT_COLOR

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

        # bubble above the player's head
        self.bubble: dict[NPC, pygame.surface.Surface] = {}
        self.cinema_x_ratio: Optional[float] = None
        self.cinema_y_ratio: Optional[float] = None

        ######################################################################
        #                       Fullscreen Animations                        #
        ######################################################################

        self.map_animations: dict[str, AnimationInfo] = {}

        if local_session.player is None:
            new_player = Player(prepare.PLAYER_NPC, world=self)
            local_session.player = new_player

        self.camera = Camera(local_session.player, self.boundary_checker)

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

    def fade_and_teleport(self, duration: float, color: ColorLike) -> None:
        """
        Fade out, teleport, fade in.

        Parameters:
            duration: Duration of the fade out. The fade in is slightly larger.
            color: Fade's color.

        """

        def cleanup() -> None:
            self.in_transition = False

        def fade_in() -> None:
            self.trigger_fade_in(duration, color)
            self.task(cleanup, duration)

        # cancel any fades that may be going one
        self.remove_animations_of(self)
        self.remove_animations_of(cleanup)

        self.stop_and_reset_char(self.player)

        self.in_transition = True
        self.trigger_fade_out(duration, color)

        task = self.task(
            partial(
                self.teleporter.handle_delayed_teleport, self, self.player
            ),
            duration,
        )
        task.chain(fade_in, duration + 0.5)

    def trigger_fade_in(self, duration: float, color: ColorLike) -> None:
        """
        World state has own fade code b/c moving maps doesn't change state.

        Parameters:
            duration: Duration of the fade in.
            color: Fade's color.

        """
        self.set_transition_surface(color)
        self.animate(
            self,
            transition_alpha=0,
            initial=255,
            duration=duration,
            round_values=True,
        )
        self.task(partial(self.unlock_controls, self.player), max(duration, 0))

    def trigger_fade_out(self, duration: float, color: ColorLike) -> None:
        """
        World state has own fade code b/c moving maps doesn't change state.

        * Will cause player to teleport if set somewhere else.

        Parameters:
            duration: Duration of the fade out.
            color: Fade's color.

        """
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

    def set_transition_surface(self, color: ColorLike) -> None:
        self.transition_surface = pygame.Surface(
            self.client.screen.get_size(), pygame.SRCALPHA
        )
        self.transition_surface.fill(color)

    def broadcast_player_teleport_change(self) -> None:
        """Tell clients/host that player has moved after teleport."""
        # Set the transition variable in event_data to false when we're done
        self.client.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        if self.client.isclient or self.client.ishost:
            self.client.add_clients_to_map(self.client.client.client.registry)
            self.client.client.update_player(self.player.facing)

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
        for anim_data in self.map_animations.values():
            anim_data["animation"].update(time_delta)
        self.camera.update()

        logger.debug("*** Game Loop Started ***")
        logger.debug("Player Variables:" + str(self.player.game_variables))
        logger.debug("Money:" + str(self.player.money))
        logger.debug("Tuxepedia:" + str(self.player.tuxepedia))

    def draw(self, surface: pygame.surface.Surface) -> None:
        """
        Draw the game world to the screen.

        Parameters:
            surface: Surface to draw into.

        """
        self.screen = surface
        self.map_drawing(surface)
        self.fullscreen_animations(surface)

    def translate_input_event(self, event: PlayerInput) -> PlayerInput:
        try:
            return PlayerInput(
                self.keymap[event.button],
                event.value,
                event.hold_time,
            )
        except KeyError:
            pass

        if event.button == events.UNICODE:
            if event.value == "n":
                return PlayerInput(
                    intentions.NOCLIP,
                    event.value,
                    event.hold_time,
                )
            if event.value == "r":
                return PlayerInput(
                    intentions.RELOAD_MAP,
                    event.value,
                    event.hold_time,
                )

        return event

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
        event = self.translate_input_event(event)

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
                return self.camera.handle_input(event)

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
    #                   Map Drawing                    #
    ####################################################
    def get_npc_surfaces(self, current_map: int) -> list[WorldSurfaces]:
        """Get the NPC surfaces/sprites."""
        npc_surfaces = []
        for npc in self.npcs:
            npc_surfaces.extend(self.get_sprites(npc, current_map))
        return npc_surfaces

    def get_map_animations(self) -> list[WorldSurfaces]:
        """Get the map animations."""
        map_animations = []
        for anim_data in self.map_animations.values():
            anim = anim_data["animation"]
            if not anim.is_finished() and anim.visibility:
                surface = anim.get_current_frame()
                vector = Vector2(anim_data["position"])
                layer = anim_data["layer"]
                map_animation = WorldSurfaces(surface, vector, layer)
                map_animations.append(map_animation)
        return map_animations

    def position_surfaces(
        self, surfaces: list[WorldSurfaces]
    ) -> list[tuple[pygame.surface.Surface, Rect, int]]:
        """Position the surfaces correctly."""
        screen_surfaces = []
        for frame in surfaces:
            surface = frame.surface
            position = frame.position3
            layer = frame.layer

            # Project to pixel/screen coordinates
            screen_position = self.get_pos_from_tilepos(position)

            # Handle tall sprites
            height = surface.get_height()
            if height > prepare.TILE_SIZE[1]:
                screen_position = (
                    screen_position[0],
                    screen_position[1] - height // 2,
                )

            rect = Rect(screen_position, surface.get_size())
            screen_surfaces.append((surface, rect, layer))
        return screen_surfaces

    def draw_map_and_sprites(
        self,
        surface: pygame.surface.Surface,
        screen_surfaces: list[tuple[pygame.surface.Surface, Rect, int]],
    ) -> None:
        """Draw the map and sprites."""
        assert self.current_map.renderer
        self.rect = self.current_map.renderer.draw(
            surface, surface.get_rect(), screen_surfaces
        )

    def apply_vertical_bars(
        self, surface: pygame.surface.Surface, aspect_ratio: float
    ) -> None:
        """
        Add vertical black bars to the top and bottom of the screen
        to achieve a cinematic aspect ratio.
        """
        screen_aspect_ratio = self.resolution[0] / self.resolution[1]
        if screen_aspect_ratio < aspect_ratio:
            bar_height = int(
                self.resolution[1]
                * (1 - screen_aspect_ratio / aspect_ratio)
                / 2
            )
            bar = pygame.Surface((self.resolution[0], bar_height))
            bar.fill(prepare.BLACK_COLOR)
            surface.blit(bar, (0, 0))
            surface.blit(bar, (0, self.resolution[1] - bar_height))

    def apply_horizontal_bars(
        self, surface: pygame.surface.Surface, aspect_ratio: float
    ) -> None:
        """
        Add horizontal black bars to the left and right of the screen
        to achieve a cinematic aspect ratio.
        """
        screen_aspect_ratio = self.resolution[1] / self.resolution[0]
        if screen_aspect_ratio < aspect_ratio:
            bar_width = int(
                self.resolution[0]
                * (1 - screen_aspect_ratio / aspect_ratio)
                / 2
            )
            bar = pygame.Surface((bar_width, self.resolution[1]))
            bar.fill(prepare.BLACK_COLOR)
            surface.blit(bar, (0, 0))
            surface.blit(bar, (self.resolution[0] - bar_width, 0))

    def set_bubble(
        self, screen_surfaces: list[tuple[pygame.surface.Surface, Rect, int]]
    ) -> None:
        if self.bubble:
            for npc, surface in self.bubble.items():
                cx, cy = self.get_pos_from_tilepos(Vector2(npc.tile_pos))
                bubble_rect = surface.get_rect()
                bubble_rect.centerx = npc.rect.centerx
                bubble_rect.bottom = npc.rect.top
                bubble_rect.x = cx
                bubble_rect.y = cy - (
                    surface.get_height() + int(npc.rect.height / 10)
                )
                bubble = (surface, bubble_rect, 100)
                screen_surfaces.append(bubble)

    def set_layer(self, surface: pygame.surface.Surface) -> None:
        self.layer.fill(self.layer_color)
        surface.blit(self.layer, (0, 0))

    def map_drawing(self, surface: pygame.surface.Surface) -> None:
        """Draw the map tiles in a layered order."""
        # Ensure map renderer is initialized
        if self.current_map.renderer is None:
            self.current_map.initialize_renderer()

        # Get player coordinates to center map
        cx, cy = self.camera.position
        assert self.current_map.renderer
        self.current_map.renderer.center((cx, cy))

        # Get NPC surfaces/sprites
        current_map = self.current_map.sprite_layer
        npc_surfaces = self.get_npc_surfaces(current_map)

        # Get map animations
        map_animations = self.get_map_animations()

        # Combine NPC surfaces and map animations
        surfaces = npc_surfaces + map_animations

        # Position surfaces correctly
        screen_surfaces = self.position_surfaces(surfaces)

        # Add bubble above player's head
        self.set_bubble(screen_surfaces)

        # Draw the map and sprites
        self.draw_map_and_sprites(surface, screen_surfaces)

        # Add transparent layer
        self.set_layer(surface)

        # Draw collision map for debug purposes
        if prepare.CONFIG.collision_map:
            self.debug_drawing(surface)

        # Apply cinema mode
        if self.cinema_x_ratio is not None:
            self.apply_horizontal_bars(surface, self.cinema_x_ratio)
        if self.cinema_y_ratio is not None:
            self.apply_vertical_bars(surface, self.cinema_y_ratio)

    def get_sprites(self, npc: NPC, layer: int) -> list[WorldSurfaces]:
        """
        Get the surfaces and layers for the sprite. Used to render the NPC.

        Parameters:
            layer: The layer to draw the sprite on.

        Returns:
            WorldSurfaces containing the surface to plot, the current
            position of the NPC and the layer.

        """

        def get_frame(d: SpriteMap, ani: str) -> pygame.surface.Surface:
            frame = d[ani]
            if isinstance(frame, SurfaceAnimation):
                surface = frame.get_current_frame()
                frame.rate = npc.moverate / prepare.CONFIG.player_walkrate
                return surface
            else:
                return frame

        frame_dict: SpriteMap = npc.sprite if npc.moving else npc.standing
        moving = "walking" if npc.moving else "idle"
        state = animation_mapping[moving][npc.facing]
        world = WorldSurfaces(
            get_frame(frame_dict, state), proj(npc.position3), layer
        )
        return [world]

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

    def get_tile_moverate(
        self,
        surface_map: MutableMapping[tuple[int, int], dict[str, float]],
        position: tuple[int, int],
    ) -> float:
        """
        Returns moverate of a specific tile from the surface map.

        If the position is not found in the map, or if the tile has no
        moverate value, returns 1.0 as the default moverate.

        Parameters:
            surface_map: The surface map.
            position: The coordinate pf the tile.

        Returns:
            The moverate of the tile at the specified position.

        """
        tile_properties = surface_map.get(position, {})
        return next(iter(tile_properties.values()), 1.0)

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
        """
        Pathfind.

        Parameters:
            start: Initial tile position.
            dest: Target tile position.

        Returns:
            Sequence of tile positions of the steps, if a path exists.
            ``None`` otherwise.

        """
        pathnode = self.pathfind_r(dest, [PathfindNode(start)], set())

        if pathnode:
            # traverse the node to get the path
            path = []
            while pathnode:
                path.append(pathnode.get_value())
                pathnode = pathnode.get_parent()

            return path[:-1]

        else:
            character = self.get_entity_pos(start)
            assert character
            logger.error(
                f"{character.name}'s pathfinding failed to find a path from "
                + f"{str(start)} to {str(dest)} in {self.current_map.filename}. "
                + "Are you sure that an obstacle-free path exists?"
            )

            return None

    def pathfind_r(
        self,
        dest: tuple[int, int],
        queue: list[PathfindNode],
        known_nodes: set[tuple[int, int]],
    ) -> Optional[PathfindNode]:
        """
        Breadth first search algorithm.

        Parameters:
            dest: Target tile position.
            queue: Queue of nodes to explore.
            known_nodes: Already explored nodes.

        Returns:
            A node with the path if it exist. ``None`` otherwise.

        """
        # The collisions shouldn't have changed whilst we were calculating,
        # so it saves time to reuse the map.
        collision_map = self.get_collision_map()
        known_nodes.add(queue[0].get_value())
        while queue:
            node = queue.pop(0)
            if node.get_value() == dest:
                return node
            else:
                for adj_pos in self.get_exits(
                    node.get_value(),
                    collision_map,
                    known_nodes,
                ):
                    if adj_pos not in known_nodes:
                        known_nodes.add(adj_pos)
                        queue.append(PathfindNode(adj_pos, node))

        return None

    def get_explicit_tile_exits(
        self,
        position: tuple[int, int],
        tile: RegionProperties,
        skip_nodes: Optional[set[tuple[int, int]]] = None,
    ) -> Optional[list[tuple[float, ...]]]:
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

        try:
            # Check if the players current position has any exit limitations.
            if tile.endure:
                direction = (
                    self.player.facing
                    if len(tile.endure) > 1 or not tile.endure
                    else tile.endure[0]
                )
                exit_position = tuple(dirs2[direction] + position)
                if exit_position not in skip_nodes:
                    return [exit_position]

            # Check if the tile explicitly defines exits.
            if tile.exit_from:
                return [
                    tuple(dirs2[direction] + position)
                    for direction in tile.exit_from
                    if tuple(dirs2[direction] + position) not in skip_nodes
                ]
        except (KeyError, TypeError):
            return None

        return None

    def get_exits(
        self,
        position: tuple[int, int],
        collision_map: Optional[CollisionMap] = None,
        skip_nodes: Optional[set[tuple[int, int]]] = None,
    ) -> Sequence[tuple[int, int]]:
        """
        Return list of tiles which can be moved into.

        This checks for adjacent tiles while checking for walls,
        npcs, and collision lines, one-way tiles, etc.

        Parameters:
            position: The original position.
            collision_map: Mapping of collisions with entities and terrain.
            skip_nodes: Set of nodes to skip.

        Returns:
            Sequence of adjacent and traversable tile positions.

        """
        # TODO: rename this
        # get tile-level and npc/entity blockers
        collision_map = collision_map or self.get_collision_map()
        skip_nodes = skip_nodes or set()

        # if there are explicit way to exit this position use that information,
        # handles 'continue' and 'exits'
        tile_data = collision_map.get(position)
        if tile_data:
            exits = self.get_explicit_tile_exits(
                position,
                tile_data,
                skip_nodes,
            )
        else:
            exits = None

        # get exits by checking surrounding tiles
        adjacent_tiles = set()
        for direction in [
            Direction.down,
            Direction.right,
            Direction.up,
            Direction.left,
        ]:
            neighbor = get_adjacent_position(position, direction)
            # if exits are defined make sure the neighbor is present there
            if exits and neighbor not in exits:
                continue

            # check if the neighbor region is present in skipped nodes
            if neighbor in skip_nodes:
                continue

            # We only need to check the perimeter,
            # as there is no way to get further out of bounds
            if not self.boundary_checker.is_within_boundaries(neighbor):
                continue

            # check to see if this tile is separated by a wall
            if (position, direction) in self.collision_lines_map:
                # there is a wall so stop checking this direction
                continue

            # test if this tile has special movement handling
            # NOTE: Do not refact. into a dict.get(xxxxx, None) style check
            # NOTE: None has special meaning in this check
            try:
                tile_data = collision_map[neighbor]
            except KeyError:
                pass
            else:
                # None means tile is blocked with no specific data
                if tile_data is None:
                    continue

                try:
                    if pairs(direction) not in tile_data.enter_from:
                        continue
                except KeyError:
                    continue

            # no tile data, so assume it is free to move into
            adjacent_tiles.add(neighbor)

        return list(adjacent_tiles)

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
