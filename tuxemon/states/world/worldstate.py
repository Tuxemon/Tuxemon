# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import itertools
import logging
import os
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Optional,
    TypedDict,
    Union,
    no_type_check,
)

import pygame
from pygame.rect import Rect

from tuxemon import networking, prepare, state
from tuxemon.db import Direction
from tuxemon.entity import Entity
from tuxemon.graphics import ColorLike
from tuxemon.map import (
    PathfindNode,
    RegionProperties,
    TuxemonMap,
    dirs2,
    pairs,
    proj,
)
from tuxemon.map_loader import TMXMapLoader, YAMLEventLoader
from tuxemon.math import Vector2
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.states.world.world_menus import WorldMenuState
from tuxemon.surfanim import SurfaceAnimation

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

        # Provide access to the screen surface
        self.screen = self.client.screen
        self.screen_rect = self.screen.get_rect()
        self.resolution = prepare.SCREEN_SIZE
        self.tile_size = prepare.TILE_SIZE
        # default variables for layer
        self.layer = pygame.Surface(
            self.client.screen.get_size(), pygame.SRCALPHA
        )
        self.layer_color: ColorLike = prepare.TRANSPARENT_COLOR

        #####################################################################
        #                           Player Details                           #
        ######################################################################

        self.npcs: list[NPC] = []
        self.npcs_off_map: list[NPC] = []
        self.wants_to_move_player: Optional[Direction] = None
        self.allow_player_movement = True

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

        # The delayed teleport variable is used to perform a teleport in the
        # middle of a transition. For example, fading to black, then
        # teleporting the player, and fading back in again.
        self.delayed_teleport = False
        self.delayed_mapname = ""
        self.delayed_x = 0
        self.delayed_y = 0

        # The delayed facing variable used to change the player's facing in
        # the middle of a transition.
        self.delayed_facing: Optional[Direction] = None

        ######################################################################
        #                       Fullscreen Animations                        #
        ######################################################################

        self.map_animations: dict[str, AnimationInfo] = {}

        if local_session.player is None:
            new_player = Player(prepare.PLAYER_NPC, world=self)
            local_session.player = new_player

        if map_name:
            self.change_map(map_name)
        else:
            raise ValueError("You must pass the map name to load")

    def resume(self) -> None:
        """Called after returning focus to this state"""
        self.unlock_controls()

    def pause(self) -> None:
        """Called before another state gets focus"""
        self.lock_controls()
        self.stop_player()

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

        self.stop_and_reset_player()

        self.in_transition = True
        self.trigger_fade_out(duration, color)

        task = self.task(self.handle_delayed_teleport, duration)
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
        self.task(self.unlock_controls, duration - 0.5)

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
        self.stop_player()
        self.lock_controls()

    def handle_delayed_teleport(self) -> None:
        """
        Call to teleport player if delayed_teleport is set.

        * Load a map
        * Move player
        * Send data to network about teleport

        """
        if self.delayed_teleport:
            self.stop_player()
            self.lock_controls()

            # check if map has changed, and if so, change it
            map_name = prepare.fetch("maps", self.delayed_mapname)

            if map_name != self.current_map.filename:
                self.change_map(map_name)

            self.player.set_position((self.delayed_x, self.delayed_y))

            if self.delayed_facing:
                self.player.facing = self.delayed_facing
                self.delayed_facing = None

            self.delayed_teleport = False

    def set_transition_surface(self, color: ColorLike) -> None:
        self.transition_surface = pygame.Surface(
            self.client.screen.get_size(), pygame.SRCALPHA
        )
        self.transition_surface.fill(color)

    def set_layer(self) -> None:
        self.layer.fill(self.layer_color)
        self.screen.blit(self.layer, (0, 0))

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
            if event.held:
                self.wants_to_move_player = direction
                if self.allow_player_movement:
                    self.move_player(direction)
                return None
            elif not event.pressed:
                if direction == self.wants_to_move_player:
                    self.stop_player()
                    return None

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
    def map_drawing(self, surface: pygame.surface.Surface) -> None:
        """
        Draws the map tiles in a layered order.

        Parameters:
            surface: Surface to draw into.

        """
        # TODO: move all drawing into a "WorldView" widget
        # interlace player sprites with tiles surfaces.
        # eventually, maybe use pygame sprites or something similar
        world_surfaces: list[WorldSurfaces] = []

        # temporary
        if self.current_map.renderer is None:
            self.current_map.initialize_renderer()

        # get player coords to center map
        cx, cy = self.project(self.player.position3)

        # offset center point for player sprite
        cx += prepare.TILE_SIZE[0] // 2
        cy += prepare.TILE_SIZE[1] // 2

        # center the map on center of player sprite
        # must center map before getting sprite coordinates
        assert self.current_map.renderer
        self.current_map.renderer.center((cx, cy))

        # get npc surfaces/sprites
        current_map = self.current_map.sprite_layer
        for npc in self.npcs:
            world_surfaces.extend(self.get_sprites(npc, current_map))

        # get map_animations
        for anim_data in self.map_animations.values():
            anim = anim_data["animation"]
            if not anim.is_finished() and anim.visibility:
                _surface = anim.get_current_frame()
                _vector = Vector2(anim_data["position"])
                _layer = anim_data["layer"]
                world_surface = WorldSurfaces(_surface, _vector, _layer)
                world_surfaces.append(world_surface)

        # position the surfaces correctly
        # pyscroll expects surfaces in screen coords, so they are
        # converted from world to screen coords here
        screen_surfaces = list()
        for frame in world_surfaces:
            s = frame.surface
            c = frame.position3
            l = frame.layer

            # project to pixel/screen coords
            _c = self.get_pos_from_tilepos(c)

            # TODO: better handling of tall sprites
            # handle tall sprites
            h = s.get_height()
            if h > prepare.TILE_SIZE[1]:
                # offset for center and image height
                _c = (_c[0], _c[1] - h // 2)

            r = Rect(_c, s.get_size())
            screen_surfaces.append((s, r, l))

        # Adds a bubble above player's head
        self.set_bubble(screen_surfaces)

        # draw the map and sprites
        self.rect = self.current_map.renderer.draw(
            surface, surface.get_rect(), screen_surfaces
        )

        # If we want to draw the collision map for debug purposes
        if prepare.CONFIG.collision_map:
            self.debug_drawing(surface)

        # If triggers night color only at night (2200-0400) outside
        game_variable = self.player.game_variables

        # Adds a transparent layer
        self.set_layer()

        if "cinema_mode" in game_variable:
            if game_variable["cinema_mode"] == "on":
                top_bar = pygame.Surface(
                    (self.resolution[0], self.resolution[1] / 6)
                )
                bottom_bar = pygame.Surface(
                    (self.resolution[0], self.resolution[1] / 6)
                )
                top_bar.fill(prepare.BLACK_COLOR)
                bottom_bar.fill(prepare.BLACK_COLOR)
                surface.blit(top_bar, (0, 0))
                bottom = surface.get_rect().bottom - self.resolution[1] / 6
                surface.blit(bottom_bar, (0, bottom))

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
        for npc in self.npcs:
            if npc.slug == slug:
                return npc
        return None

    def get_entity_by_iid(self, iid: uuid.UUID) -> Optional[NPC]:
        """
        Get an entity from the world.

        Parameters:
            iid: The entity iid.

        """
        for npc in self.npcs:
            if npc.instance_id == iid:
                return npc
        return None

    def get_entity_pos(self, pos: tuple[int, int]) -> Optional[NPC]:
        """
        Get an entity from the world by its position.

        Parameters:
            pos: The entity position.

        """
        for npc in self.npcs:
            if npc.tile_pos == pos:
                return npc
        return None

    def remove_entity(self, slug: str) -> None:
        """
        Remove an entity from the world.

        Parameters:
            slug: The entity slug.

        """
        for npc in self.npcs:
            if npc.slug == slug:
                npc.remove_collision(npc.tile_pos)
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
        monsters = []
        for npc in self.npcs:
            for monster in npc.monsters:
                monsters.append(monster)
        return monsters

    def get_monster_by_iid(self, iid: uuid.UUID) -> Optional[Monster]:
        """
        Get a monster from the world.

        Parameters:
            iid: The monster iid.

        """
        for monster in self.get_all_monsters():
            if monster.instance_id == iid:
                return monster
        return None

    def get_all_tile_properties(
        self,
        map: MutableMapping[tuple[int, int], dict[str, float]],
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Returns coords (tuple) of specific tile property.

        Parameters:
            map: The surface map.
            label: The label (SurfaceKeys).

        Returns:
            The coordinates.

        """
        tiles = [coords for coords, props in map.items() if label in props]
        return tiles

    def get_tile_moverate(
        self,
        map: MutableMapping[tuple[int, int], dict[str, float]],
        position: tuple[int, int],
    ) -> float:
        """
        Returns moverate of a specific tile by looking in surface map.

        Parameters:
            map: The surface map.
            position: The coordinate.

        Returns:
            Moverate (float), default 1.0

        """
        moverate = 1.0
        for coord, props in map.items():
            if coord == position:
                moverate = float(next(iter(props.values())))
        return moverate

    def check_collision_zones(
        self,
        map: MutableMapping[tuple[int, int], Optional[RegionProperties]],
        label: str,
    ) -> list[tuple[int, int]]:
        """
        Returns coords (tuple) of specific collision zones.

        Returns:
            The coordinates.

        """
        tiles = []
        for coords, props in map.items():
            if props and props.key and props.key == label:
                tiles.append(coords)
        return tiles

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
        # TODO: overlapping tiles/objects by returning a list
        collision_dict: CollisionDict = {}

        # Get all the NPCs' tile positions
        for npc in self.get_all_entities():
            region = self.collision_map.get(npc.tile_pos)
            if region:
                prop = RegionProperties(
                    region.enter_from,
                    region.exit_from,
                    region.endure,
                    npc,
                    region.key,
                )
            else:
                prop = RegionProperties(
                    enter_from=[],
                    exit_from=[],
                    endure=[],
                    entity=npc,
                    key=None,
                )
            collision_dict[npc.tile_pos] = prop

        for coords, surface in self.surface_map.items():
            region = self.collision_map.get(coords)
            for label, value in surface.items():
                if region:
                    _prop = RegionProperties(
                        region.enter_from,
                        region.exit_from,
                        region.endure,
                        region.entity,
                        label,
                    )
                else:
                    _prop = RegionProperties(
                        enter_from=[],
                        exit_from=[],
                        endure=[],
                        entity=None,
                        key=label,
                    )
                if float(value) == 0:
                    collision_dict[coords] = _prop

        # tile layout takes precedence
        collision_dict.update(self.collision_map)

        return collision_dict

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
        pathnode = self.pathfind_r(
            dest,
            [PathfindNode(start)],
            set(),
        )

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
                    new_node = PathfindNode(adj_pos, node)
                    known_nodes.add(new_node.get_value())
                    queue.append(new_node)

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
        # Check if the players current position has any exit limitations.
        # this check is for tiles which define the only way to exit.
        # for instance, one-way tiles.

        # does the tile define continue movements?
        try:
            if tile.endure:
                _direction = (
                    self.player.facing
                    if len(tile.endure) > 1 or not tile.endure
                    else tile.endure[0]
                )
                return [tuple(dirs2[_direction] + position)]
            else:
                pass
        except KeyError:
            pass

        # does the tile explicitly define exits?
        try:
            adjacent_tiles = list()
            if tile.exit_from:
                for direction in tile.exit_from:
                    exit_tile = tuple(dirs2[direction] + position)
                    if skip_nodes and exit_tile in skip_nodes:
                        continue
                    adjacent_tiles.append(exit_tile)
                return adjacent_tiles
        except KeyError:
            pass

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
            position: Original position.
            collision_map: Mapping of collisions with entities and terrain.
            skip_nodes: Set of nodes to skip.

        Returns:
            Sequence of adjacent and traversable tile positions.

        """
        # TODO: rename this
        # get tile-level and npc/entity blockers
        if collision_map is None:
            collision_map = self.get_collision_map()

        if skip_nodes is None:
            skip_nodes = set()

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
        adjacent_tiles = list()
        for direction, neighbor in (
            (Direction.down, (position[0], position[1] + 1)),
            (Direction.right, (position[0] + 1, position[1])),
            (Direction.up, (position[0], position[1] - 1)),
            (Direction.left, (position[0] - 1, position[1])),
        ):
            # if exits are defined make sure the neighbor is present there
            if exits and neighbor not in exits:
                continue

            # check if the neighbor region is present in skipped nodes
            if neighbor in skip_nodes:
                continue

            # We only need to check the perimeter,
            # as there is no way to get further out of bounds
            if not (
                self.invalid_x[0] < neighbor[0] < self.invalid_x[1]
            ) or not (self.invalid_y[0] < neighbor[1] < self.invalid_y[1]):
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
            adjacent_tiles.append(neighbor)

        return adjacent_tiles

    ####################################################
    #                Player Movement                   #
    ####################################################
    def lock_controls(self) -> None:
        """Prevent input from moving the player."""
        self.allow_player_movement = False

    def unlock_controls(self) -> None:
        """
        Allow the player to move.

        If the player was previously holding a direction down,
        then the player will start moving after this is called.

        """
        self.allow_player_movement = True
        if self.wants_to_move_player:
            self.move_player(self.wants_to_move_player)

    def stop_player(self) -> None:
        """
        Reset controls and stop player movement at once. Do not lock controls.

        Movement is gracefully stopped.  If player was in a movement, then
        complete it before stopping.

        """
        self.wants_to_move_player = None
        self.client.release_controls()
        self.player.cancel_movement()

    def stop_and_reset_player(self) -> None:
        """
        Reset controls, stop player and abort movement. Do not lock controls.

        Movement is aborted here, so the player will not complete movement
        to a tile.  It will be reset to the tile where movement started.

        Use if you don't want to trigger another tile event.

        """
        self.wants_to_move_player = None
        self.client.release_controls()
        self.player.abort_movement()

    def move_player(self, direction: Direction) -> None:
        """
        Move player in a direction. Changes facing.

        Parameters:
            direction: New direction of the player.

        """
        self.player.move_direction = direction

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
        px, py = self.project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def project(
        self,
        position: Sequence[float],
    ) -> tuple[int, int]:
        return (
            int(position[0] * self.tile_size[0]),
            int(position[1] * self.tile_size[1]),
        )

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
            size = self.project((event.w, event.h))
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
        # Set the currently loaded map. This is needed because the event
        # engine loads event conditions and event actions from the currently
        # loaded map. If we change maps, we need to update this.
        logger.debug("Map was not preloaded. Loading from disk.")
        map_data = self.load_map(map_name)

        self.current_map = map_data
        self.collision_map = map_data.collision_map
        self.surface_map = map_data.surface_map
        self.collision_lines_map = map_data.collision_lines_map
        self.map_size = map_data.size
        self.map_area = map_data.area

        # The first coordinates that are out of bounds.
        self.invalid_x = (-1, self.map_size[0])
        self.invalid_y = (-1, self.map_size[1])

        self.client.load_map(map_data)

        # Clear out any existing NPCs
        self.npcs = []
        self.npcs_off_map = []
        self.add_player(local_session.player)

        # reset controls and stop moving to prevent player from
        # moving after the teleport and being out of game
        self.stop_player()

        # move to spawn position, if any
        for eo in self.client.events:
            if eo.name.lower() == "player spawn":
                self.player.set_position((eo.x, eo.y))
                self.player.remove_collision((eo.x, eo.y))

    def load_map(self, path: str) -> TuxemonMap:
        """
        Returns map data as a dictionary to be used for map changing.

        Parameters:
            path: Path of the map to load.

        Returns:
            Loaded map.

        """
        txmn_map = TMXMapLoader().load(path)
        yaml_path = path[:-4] + ".yaml"
        _paths = [yaml_path]

        if txmn_map.scenario:
            _scenario = prepare.fetch("maps", txmn_map.scenario + ".yaml")
            _paths.append(_scenario)

        _events = list(txmn_map.events)
        _inits = list(txmn_map.inits)
        for _path in _paths:
            if os.path.exists(_path):
                _events.extend(YAMLEventLoader().load_events(_path, "event"))
                _inits.extend(YAMLEventLoader().load_events(_path, "init"))

        txmn_map.events = _events
        txmn_map.inits = _inits
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
