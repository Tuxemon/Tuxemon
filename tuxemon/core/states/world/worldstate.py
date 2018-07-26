# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
# core.states.world Handles the world map and player movement.
#
#
from __future__ import division

import itertools
import logging

import pygame
from six.moves import map as imap

from tuxemon.core import prepare, state
from tuxemon.core.components import networking
from tuxemon.core.components.game_event import GAME_EVENT, INPUT_EVENT
from tuxemon.core.components.map import PathfindNode, Map, dirs2, pairs
from tuxemon.core.tools import nearest

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

keymap = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",

}

class WorldState(state.State):
    """ The state responsible for the world game play
    """

    preloaded_maps = {}

    def startup(self):
        # Provide access to the screen surface
        self.screen = self.game.screen
        self.screen_rect = prepare.SCREEN_RECT
        self.resolution = prepare.SCREEN_SIZE
        self.tile_size = prepare.TILE_SIZE

        #####################################################################
        #                           Player Details                           #
        ######################################################################

        self.npcs = {}
        self.npcs_off_map = {}
        self.player1 = None
        self.wants_to_move_player = None
        self.allow_player_movement = True

        ######################################################################
        #                              Map                                   #
        ######################################################################

        # Keep a map of preloaded maps for fast map switching.
        self.preloaded_maps = {}
        self.current_map = None

        ######################################################################
        #                            Transitions                             #
        ######################################################################

        # default variables for transition
        self.transition_alpha = 0
        self.transition_surface = None
        self.in_transition = False

        # The delayed teleport variable is used to perform a teleport in the
        # middle of a transition. For example, fading to black, then
        # teleporting the player, and fading back in again.
        self.delayed_teleport = False

        # The delayed facing variable used to change the player's facing in
        # the middle of a transition.
        self.delayed_facing = None

        ######################################################################
        #                       Fullscreen Animations                        #
        ######################################################################

        # The cinema bars are used for cinematic moments.
        # The cinema state can be: "off", "on", "turning on" or "turning off"
        self.cinema_state = "off"
        self.cinema_speed = 15 * prepare.SCALE  # Pixels per second speed of the animation.

        self.cinema_top = {}
        self.cinema_bottom = {}

        # Create a surface that we'll use as black bars for a cinematic
        # experience
        self.cinema_top['surface'] = pygame.Surface(
            (self.resolution[0], self.resolution[1] / 6))
        self.cinema_bottom['surface'] = pygame.Surface(
            (self.resolution[0], self.resolution[1] / 6))

        # Fill our empty surface with black
        self.cinema_top['surface'].fill((0, 0, 0))
        self.cinema_bottom['surface'].fill((0, 0, 0))

        # When cinema mode is off, this will be the position we'll draw the
        # black bar.
        self.cinema_top['off_position'] = [
            0, -self.cinema_top['surface'].get_height()]
        self.cinema_bottom['off_position'] = [0, self.resolution[1]]
        self.cinema_top['position'] = list(self.cinema_top['off_position'])
        self.cinema_bottom['position'] = list(
            self.cinema_bottom['off_position'])

        # When cinema mode is ON, this will be the position we'll draw the
        # black bar.
        self.cinema_top['on_position'] = [0, 0]
        self.cinema_bottom['on_position'] = [
            0, self.resolution[1] - self.cinema_bottom['surface'].get_height()]

        self.map_animations = dict()

    def fade_and_teleport(self, duration=2):
        """ Fade out, teleport, fade in

        :return:
        """

        def cleanup():
            self.in_transition = False

        def fade_in():
            self.trigger_fade_in(duration)
            self.task(cleanup, duration)

        # cancel any fades that may be going one
        self.remove_animations_of(self)
        self.remove_animations_of(cleanup)

        # stop player movement
        self.player1.cancel_movement()

        self.in_transition = True
        self.trigger_fade_out(duration)

        task = self.task(self.handle_delayed_teleport, duration)
        task.chain(fade_in, duration + .5)

    def trigger_fade_in(self, duration=2):
        """ World state has own fade code b/c moving maps doesn't change state

        :returns: None
        """
        self.set_transition_surface()
        self.animate(self, transition_alpha=0, initial=255, duration=duration, round_values=True)
        self.task(self.unlock_controls, duration - .5)  # unlock controls before fade ends

    def trigger_fade_out(self, duration=2):
        """ World state has own fade code b/c moving maps doesn't change state

        * will cause player to teleport if set somewhere else

        :returns: None
        """
        self.set_transition_surface()
        self.animate(self, transition_alpha=255, initial=0, duration=duration, round_values=True)
        self.lock_controls()

    def handle_delayed_teleport(self):
        """ Call to teleport player if delayed_teleport is set

        * load a map
        * move player
        * send data to network about teleport

        :return: None
        """
        if self.delayed_teleport:
            self.player1.cancel_movement()
            self.lock_controls()

            # check if map has changed, and if so, change it
            map_name = prepare.BASEDIR + prepare.DATADIR + "/maps/" + self.delayed_mapname
            if map_name != self.current_map.filename:
                self.change_map(map_name)

            self.player1.set_position((self.delayed_x, self.delayed_y))

            if self.delayed_facing:
                self.player1.facing = self.delayed_facing
                self.delayed_facing = None

            self.delayed_teleport = False

    def set_transition_surface(self, color=(0, 0, 0)):
        self.transition_surface = pygame.Surface(self.game.screen.get_size())
        self.transition_surface.fill(color)

    def broadcast_player_teleport_change(self):
        """ Tell clients/host that player has moved or changed map after teleport

        :return:
        """
        # Set the transition variable in event_data to false when we're done
        self.game.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        if self.game.isclient or self.game.ishost:
            self.game.add_clients_to_map(self.game.client.client.registry)
            self.game.client.update_player(self.player1.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.npcs.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.game)

        for npc in self.npcs_off_map.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.game)

    def update(self, time_delta):
        """The primary game loop that executes the world's game functions every frame.

        :param time_delta: Amount of time passed since last frame.

        :type time_delta: Float

        :rtype: None
        :returns: None

        """
        super(WorldState, self).update(time_delta)
        logger.debug("*** Game Loop Started ***")
        logger.debug("Player Variables:" + str(self.player1.game_variables))

    def draw(self, surface):
        """ Draw the game world to the screen

        :param surface:
        :return:
        """
        self.screen = surface
        self.player_movement()
        self.move_npcs()
        self.map_drawing(surface)
        self.fullscreen_animations(surface)

    def process_event(self, event):
        """Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return if you have handled input here.

        :param event: A pygame key event from pygame.event.get()
        :type event: pygame.event.Event

        :rtype: None
        :returns: None

        """
        # Handle Key DOWN events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                logger.info("Opening main menu!")
                self.game.push_state("WorldMenuState")
                return

            # If we receive an arrow key press, set the facing and
            # moving direction to that direction
            # TODO: move to some generic "InputManager' type class
            for key, direction in keymap.items():
                if event.key == key:
                    self.wants_to_move_player = direction
                    if self.allow_player_movement:
                        self.move_player(direction)
                    return

            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                # TODO: Check to see if we have network players to interact with.
                multiplayer = False
                if multiplayer:
                    self.check_interactable_space()

        # Handle Key UP events
        if event.type == pygame.KEYUP:
            # If the player lets go of the key, set the moving
            # direction to false to stop movement
            direction = keymap.get(event.key)
            if direction == self.wants_to_move_player:
                self.wants_to_move_player = None
                self.player1.cancel_movement()
                return

        # Handle text input events
        if event.type == GAME_EVENT and event.event_type == INPUT_EVENT:
            self.player1.name = event.text
            return

        # if we made it this far, return the event for others to use
        return event

    ####################################################
    #                   Map Drawing                    #
    ####################################################
    def map_drawing(self, surface):
        """Draws the map tiles in a layered order.

        :param: None

        :rtype: None
        :returns: None

        """
        # TODO: move all drawing into a "WorldView" widget
        # interlace player sprites with tiles surfaces.
        # eventually, maybe use pygame sprites or something similar
        world_surfaces = list()

        # get player coords to center map
        cx, cy = nearest(self.project(self.player1.tile_pos))

        # offset center point for player sprite
        cx += prepare.TILE_SIZE[0] // 2
        cy += prepare.TILE_SIZE[1] // 2

        # center the map on center of player sprite
        # must center map before getting sprite coordinates
        self.current_map.renderer.center((cx, cy))

        # get npc surfaces/sprites
        for npc in self.npcs:
            world_surfaces.extend(self.npcs[npc].get_sprites())

        # get map_animations
        for anim_data in self.map_animations.values():
            anim = anim_data['animation']
            if not anim.isFinished() and anim.visibility:
                frame = (anim.getCurrentFrame(), anim_data["position"], anim_data['layer'])
                world_surfaces.append(frame)

        # position the surfaces correctly
        # pyscroll expects surfaces in screen coords, so they are
        # converted from world to screen coords here
        screen_surfaces = list()
        for frame in world_surfaces:
            s, c, l = frame

            # project to pixel/screen coords
            c = self.get_pos_from_tilepos(c)

            # TODO: better handling of tall sprites
            # handle tall sprites
            h = s.get_height()
            if h > prepare.TILE_SIZE[1]:
                # offset for center and image height
                c = nearest((c[0], c[1] - h // 2))

            screen_surfaces.append((s, c, l))

        # draw the map and sprites
        self.current_map.renderer.draw(surface, surface.get_rect(), screen_surfaces)

        # If we want to draw the collision map for debug purposes
        if prepare.CONFIG.collision_map == "1":
            self.debug_drawing(surface)

    ####################################################
    #            Pathfinding and Collisions            #
    ####################################################
    """
    eventually refactor pathing/collisions into a more generic class
    so it doesn't rely on a running game, players, or a screen
    """

    def add_player(self, player):
        """ WIP.  Eventually handle players coming and going (for server)

        :param player:
        :return:
        """
        self.player1 = player
        self.add_entity(player)

    def add_entity(self, entity):
        """

        :type entity: core.components.entity.Entity
        :return:
        """
        entity.world = self
        self.npcs[entity.slug] = entity

    def get_entity(self, slug):
        """

        :type slug: str
        :return:
        """
        return self.npcs.get(slug)

    def remove_entity(self, slug):
        """

        :type slug: str
        :return:
        """
        del self.npcs[slug]

    def get_all_entities(self):
        """ List of players and NPCs, for collision checking

        :return:
        """
        return self.npcs.values()

    def get_collision_map(self):
        """ Return dictionary for collision testing

        Returns a dictionary where keys are (x, y) tile tuples
        and the values are tiles or NPCs.

        # NOTE:
        This will not respect map changes to collisions
        after the map has been loaded!

        :rtype: dict
        :returns: A dictionary of collision tiles
        """
        # TODO: overlapping tiles/objects by returning a list
        collision_dict = dict()

        # Get all the NPCs' tile positions
        for npc in self.get_all_entities():
            pos = nearest(npc.tile_pos)
            collision_dict[pos] = {"entity": npc}

        # tile layout takes precedence
        collision_dict.update(self.collision_map)

        return collision_dict

    def pathfind(self, start, dest):
        """ Pathfind

        :param start:
        :type dest: tuple

        :return:
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
            # TODO: get current map name for a more useful error
            logger.error("Pathfinding failed to find a path from " +
                         str(start) + " to " + str(dest) +
                         ". Are you sure that an obstacle-free path exists?")

    def pathfind_r(self, dest, queue, known_nodes):
        """ Breadth first search algorithm

        :type dest: tuple
        :type queue: list
        :type known_nodes: set

        :rtype: list
        """
        # The collisions shouldn't have changed whilst we were calculating,
        # so it saves time to reuse the map.
        collision_map = self.get_collision_map()
        while queue:
            node = queue.pop(0)
            if node.get_value() == dest:
                return node
            else:
                for adj_pos in self.get_exits(node.get_value(), collision_map, known_nodes):
                    new_node = PathfindNode(adj_pos, node)
                    known_nodes.add(new_node.get_value())
                    queue.append(new_node)

    def get_explicit_tile_exits(self, position, tile, skip_nodes):
        """ Check for exits from tile which are defined in the map

        This will return exits which were defined by the map creator

        Checks "continue" and "exits" properties of the tile

        :param position: tuple
        :param tile:
        :param skip_nodes: set
        :return: list
        """
        # Check if the players current position has any exit limitations.
        # this check is for tiles which define the only way to exit.
        # for instance, one-way tiles.

        # does the tile define continue movements?
        try:
            return [tuple(dirs2[tile['continue']] + position)]
        except KeyError:
            pass

        # does the tile explicitly define exits?
        try:
            adjacent_tiles = list()
            for direction in tile["exit"]:
                exit_tile = tuple(dirs2[direction] + position)
                if exit_tile in skip_nodes:
                    continue

                adjacent_tiles.append(exit_tile)
            return adjacent_tiles
        except KeyError:
            pass

    def get_exits(self, position, collision_map=None, skip_nodes=None):
        """ Return list of tiles which can be moved into

        This checks for adjacent tiles while checking for walls,
        npcs, and collision lines, one-way tiles, etc

        :param position: tuple
        :param collision_map: dict
        :param skip_nodes: set

        :rtype: list
        """
        # get tile-level and npc/entity blockers
        if collision_map is None:
            collision_map = self.get_collision_map()

        if skip_nodes is None:
            skip_nodes = set()

        # if there are explicit way to exit this position use that
        # information only and do not check surrounding tiles.
        # handles 'continue' and 'exits'
        tile_data = collision_map.get(position)
        if tile_data:
            exits = self.get_explicit_tile_exits(position, tile_data, skip_nodes)
            if exits:
                return exits

        # get exits by checking surrounding tiles
        adjacent_tiles = list()
        for direction, neighbor in (
                ("down", (position[0], position[1] + 1)),
                ("right", (position[0] + 1, position[1])),
                ("up", (position[0], position[1] - 1)),
                ("left", (position[0] - 1, position[1])),
        ):
            if neighbor in skip_nodes:
                continue

            # We only need to check the perimeter,
            # as there is no way to get further out of bounds
            if position[0] in self.invalid_x or position[1] in self.invalid_y:
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
                    if pairs[direction] not in tile_data['enter']:
                        continue
                except KeyError:
                    continue

            # no tile data, so assume it is free to move into
            adjacent_tiles.append(neighbor)

        return adjacent_tiles

    ####################################################
    #                Player Movement                   #
    ####################################################
    def player_movement(self):
        """Handles player's movement

        :returns: None
        """
        # Get all the keys pressed for modifiers only!
        pressed = list(pygame.key.get_pressed())
        self.ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        self.alt_held = pressed[pygame.K_LALT] or pressed[pygame.K_RALT]
        self.shift_held = pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]

        # TODO: phase out in favor of a global game clock
        self.time_passed_seconds = self.game.time_passed_seconds

        # Handle tile based movement for the player
        # TODO: move to some generic "InputManager' type class
        if self.shift_held:
            self.player1.running = True
            self.player1.walking = False
        else:
            self.player1.running = False
            self.player1.walking = True

    def lock_controls(self):
        """ Prevent input from moving the player

        :return:
        """
        self.allow_player_movement = False

    def unlock_controls(self):
        """ Allow the player to move

        If the player was previously holding a direction down,
        then the player will start moving after this is called.

        :return:
        """
        self.allow_player_movement = True
        if self.wants_to_move_player:
            self.move_player(self.wants_to_move_player)

    def move_player(self, direction):
        """ Move player in a direction.  Changes facing.

        :param direction:
        :return:
        """
        # tell the npc we want to change directions
        self.player1.move_direction = direction

    def get_pos_from_tilepos(self, tile_position):
        """ Returns the map pixel coordinate based on tile position.

        USE this to draw to the screen

        :param tile_position: An [x, y] tile position.

        :type tile_position: List

        :rtype: List
        :returns: The pixel coordinates to draw at the given tile position.
        """
        cx, cy = self.current_map.renderer.get_center_offset()
        px, py = self.project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def project(self, position):
        return position[0] * self.tile_size[0], position[1] * self.tile_size[1]

    def move_npcs(self):
        """ Move NPCs and Players around according to their state

        :return:
        """
        # TODO: This function may be moved to a server
        # Draw any game NPC's
        for entity in self.get_all_entities():
            entity.move(self.time_passed_seconds)

            if entity.update_location:
                char_dict = {"tile_pos": entity.final_move_dest}
                networking.update_client(entity, char_dict, self.game)
                entity.update_location = False

        # Move any multiplayer characters that are off map so we know where they should be when we change maps.
        for entity in self.npcs_off_map.values():
            entity.move(self.time_passed_seconds, self)

    def _collision_box_to_pgrect(self, box):
        """Returns a pygame.Rect (in screen-coords) version of a collision box (in world-coords).
        """

        # For readability
        x, y = self.get_pos_from_tilepos(box)
        tw, th = self.tile_size

        return pygame.Rect(x, y, tw, th)

    def _npc_to_pgrect(self, npc):
        """Returns a pygame.Rect (in screen-coords) version of an NPC's bounding box.
        """
        pos = self.get_pos_from_tilepos(npc.tile_pos)
        return pygame.Rect(pos, self.tile_size)

    ####################################################
    #                Debug Drawing                     #
    ####################################################
    def debug_drawing(self, surface):
        from pygame.gfxdraw import box

        surface.lock()

        # draw events
        for event in self.game.events:
            topleft = self.get_pos_from_tilepos((event.x, event.y))
            size = self.project((event.w, event.h))
            rect = topleft, size
            box(surface, rect, (0, 255, 0, 128))

        # We need to iterate over all collidable objects.  So, let's start
        # with the walls/collision boxes.
        box_iter = imap(self._collision_box_to_pgrect, self.collision_map)

        # Next, deal with solid NPCs.
        npc_iter = imap(self._npc_to_pgrect, self.npcs.values())

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

    def midscreen_animations(self, surface):
        """Handles midscreen animations that will be drawn UNDER menus and dialog.

        :param surface: surface to draw on

        :rtype: None
        :returns: None

        """

        if self.cinema_state == "turning on":

            self.cinema_top['position'][
                1] += self.cinema_speed * self.time_passed_seconds
            self.cinema_bottom['position'][
                1] -= self.cinema_speed * self.time_passed_seconds

            # If we've reached our target position, stop the animation.
            if self.cinema_top['position'] >= self.cinema_top['on_position']:
                self.cinema_top['position'] = list(
                    self.cinema_top['on_position'])
                self.cinema_bottom['position'] = list(
                    self.cinema_bottom['on_position'])

                self.cinema_state = "on"

            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

        elif self.cinema_state == "on":
            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

        elif self.cinema_state == "turning off":

            self.cinema_top['position'][1] -= (
                    self.cinema_speed * self.time_passed_seconds)
            self.cinema_bottom['position'][
                1] += self.cinema_speed * self.time_passed_seconds

            # If we've reached our target position, stop the animation.
            if self.cinema_top['position'][1] <= self.cinema_top['off_position'][1]:
                self.cinema_top['position'] = list(
                    self.cinema_top['off_position'])
                self.cinema_bottom['position'] = list(
                    self.cinema_bottom['off_position'])

                self.cinema_state = "off"

            # Draw the cinema bars
            surface.blit(
                self.cinema_top['surface'], self.cinema_top['position'])
            surface.blit(
                self.cinema_bottom['surface'], self.cinema_bottom['position'])

    ####################################################
    #         Full Screen Animations Functions         #
    ####################################################
    def fullscreen_animations(self, surface):
        """Handles fullscreen animations such as transitions, cutscenes, etc.

        :param surface: Surface to draw onto

        :rtype: None
        :returns: None

        """
        if self.in_transition:
            self.transition_surface.set_alpha(self.transition_alpha)
            surface.blit(self.transition_surface, (0, 0))

    ####################################################
    #             Map Change/Load Functions            #
    ####################################################
    def change_map(self, map_name):
        # Set the currently loaded map. This is needed because the event
        # engine loads event conditions and event actions from the currently
        # loaded map. If we change maps, we need to update this.
        if map_name not in self.preloaded_maps.keys():
            logger.debug("Map was not preloaded. Loading from disk.")
            map_data = self.load_map(map_name)
        else:
            logger.debug("%s was found in preloaded maps." % map_name)
            map_data = self.preloaded_maps[map_name]
            self.clear_preloaded_maps()

        self.current_map = map_data["data"]
        self.collision_map = map_data["collision_map"]
        self.collision_lines_map = map_data["collision_lines_map"]
        self.map_size = map_data["map_size"]

        # The first coordinates that are out of bounds.
        self.invalid_x = (-1, self.map_size[0] + 1)
        self.invalid_y = (-1, self.map_size[1] + 1)

        # TODO: remove this monkey [patching!] business for the main control/game
        self.game.events = map_data["events"]
        self.game.inits = map_data["inits"]
        self.game.interacts = map_data["interacts"]
        self.game.event_engine.reset()
        self.game.event_engine.current_map = map_data

        # Clear out any existing NPCs
        self.npcs = {}
        self.npcs_off_map = {}
        self.add_player(self.game.player1)

        # reset controls and stop moving to prevent player from
        # moving after the teleport and being out of control
        self.player1.cancel_movement()

        # move to spawn position, if any
        for eo in self.game.events:
            if eo.name.lower() == "player spawn":
                self.player1.set_position((eo.x, eo.y))

    def load_map(self, map_name):
        """ Returns map data as a dictionary to be used for map changing and preloading
        """
        map_data = {}
        map_data["data"] = Map(map_name)
        map_data["events"] = map_data["data"].events
        map_data["inits"] = map_data["data"].inits
        map_data["interacts"] = map_data["data"].interacts
        map_data["collision_map"], map_data["collision_lines_map"], map_data["map_size"] = \
            map_data["data"].loadfile()

        return map_data

    def preload_map(self, map_name):
        """ Preload a map for quicker access

        :param map_name:
        :return: None
        """
        self.preloaded_maps[map_name] = self.load_map(map_name)

    def clear_preloaded_maps(self):
        """ Clear the preloaded maps cache

        :return: None
        """
        self.preloaded_maps = {}

    def check_interactable_space(self):
        """Checks to see if any Npc objects around the player are interactable. It then populates a menu
        of possible actions.

        :param: None

        :rtype: Bool
        :returns: True if there is an Npc to interact with.

        """
        collision_dict = self.player1.get_collision_map(self)
        player_tile_pos = nearest(self.player1.tile_pos)
        collisions = self.player1.collision_check(player_tile_pos, collision_dict, self.collision_lines_map)
        if not collisions:
            pass
        else:
            for direction in collisions:
                if self.player1.facing == direction:
                    if direction == "up":
                        tile = (player_tile_pos[0], player_tile_pos[1] - 1)
                    elif direction == "down":
                        tile = (player_tile_pos[0], player_tile_pos[1] + 1)
                    elif direction == "left":
                        tile = (player_tile_pos[0] - 1, player_tile_pos[1])
                    elif direction == "right":
                        tile = (player_tile_pos[0] + 1, player_tile_pos[1])
                    for npc in self.npcs.values():
                        tile_pos = (int(round(npc.tile_pos[0])), int(round(npc.tile_pos[1])))
                        if tile_pos == tile:
                            logger.info("Opening interaction menu!")
                            self.game.push_state("InteractionMenu")
                            return True
                        else:
                            continue

    def handle_interaction(self, event_data, registry):
        """Presents options window when another player has interacted with this player.

        :param event_data: Information on the type of interaction and who sent it.
        :param registry:

        :type event_data: Dictionary
        :type registry: Dictionary

        :rtype: None
        :returns: None
        """
        target = registry[event_data["target"]]["sprite"]
        target_name = str(target.name)
        networking.update_client(target, event_data["char_dict"], self.game)
        if event_data["interaction"] == "DUEL":
            if not event_data["response"]:
                self.interaction_menu.visible = True
                self.interaction_menu.interactable = True
                self.interaction_menu.player = target
                self.interaction_menu.interaction = "DUEL"
                self.interaction_menu.menu_items = [target_name + " would like to Duel!", "Accept", "Decline"]
            else:
                if self.wants_duel:
                    if event_data["response"] == "Accept":
                        world = self.game.current_state
                        pd = world.player1.__dict__
                        event_data = {"type": "CLIENT_INTERACTION",
                                      "interaction": "START_DUEL",
                                      "target": [event_data["target"]],
                                      "response": None,
                                      "char_dict": {"monsters": pd["monsters"],
                                                    "inventory": pd["inventory"]
                                                    }

                                      }
                        self.game.server.notify_client_interaction(cuuid, event_data)
