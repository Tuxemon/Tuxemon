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

import itertools
import logging

import pygame
from six.moves import map as imap

from tuxemon.compat import Rect
from tuxemon.core import prepare, state, networking
from tuxemon.core.map import PathfindNode, TuxemonMap, dirs2, pairs
from tuxemon.core.map_loader import TMXMapLoader
from tuxemon.core.platform.const import buttons, events, intentions
from tuxemon.core.session import local_session
from tuxemon.core.tools import nearest

logger = logging.getLogger(__name__)

direction_map = {
    intentions.UP: "up",
    intentions.DOWN: "down",
    intentions.LEFT: "left",
    intentions.RIGHT: "right",
}


class WorldState(state.State):
    """ The state responsible for the world game play
    """

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

    def startup(self):
        # Provide access to the screen surface
        self.screen = self.client.screen
        self.screen_rect = self.screen.get_rect()
        self.resolution = prepare.SCREEN_SIZE
        self.tile_size = prepare.TILE_SIZE

        #####################################################################
        #                           Player Details                           #
        ######################################################################

        self.npcs = {}
        self.npcs_off_map = {}
        self.player = None
        self.wants_to_move_player = None
        self.allow_player_movement = True

        ######################################################################
        #                              Map                                   #
        ######################################################################

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

    def resume(self):
        """ Called after returning focus to this state
        """
        self.unlock_controls()

    def pause(self):
        """ Called before another state gets focus
        """
        self.lock_controls()
        self.stop_player()

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

        self.stop_player()

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
        self.stop_player()
        self.lock_controls()

    def handle_delayed_teleport(self):
        """ Call to teleport player if delayed_teleport is set

        * load a map
        * move player
        * send data to network about teleport

        :return: None
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

    def set_transition_surface(self, color=(0, 0, 0)):
        self.transition_surface = pygame.Surface(self.client.screen.get_size())
        self.transition_surface.fill(color)

    def broadcast_player_teleport_change(self):
        """ Tell clients/host that player has moved or changed map after teleport

        :return:
        """
        # Set the transition variable in event_data to false when we're done
        self.client.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        if self.client.isclient or self.client.ishost:
            self.client.add_clients_to_map(self.client.client.client.registry)
            self.client.client.update_player(self.player.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.npcs.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

        for npc in self.npcs_off_map.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.client)

    def update(self, time_delta):
        """The primary game loop that executes the world's game functions every frame.

        :param time_delta: Amount of time passed since last frame.

        :type time_delta: Float

        :rtype: None
        :returns: None

        """
        super().update(time_delta)
        self.move_npcs(time_delta)
        logger.debug("*** Game Loop Started ***")
        logger.debug("Player Variables:" + str(self.player.game_variables))

    def draw(self, surface):
        """ Draw the game world to the screen

        :param surface:
        :return:
        """
        self.screen = surface
        self.map_drawing(surface)
        self.fullscreen_animations(surface)

    def translate_input_event(self, event):
        """

        :type event: tuxemon.core.input.events.PlayerInput
        :rtype: tuxemon.core.input.events.PlayerInput
        """
        from tuxemon.core.platform.events import PlayerInput

        try:
            return PlayerInput(self.keymap[event.button], event.value, event.hold_time)
        except KeyError:
            pass

        if event.button == events.UNICODE:
            if event.value == "n":
                return PlayerInput(intentions.NOCLIP, event.value, event.hold_time)

        return event

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        event = self.translate_input_event(event)

        if event.button == intentions.WORLD_MENU:
            if event.pressed:
                logger.info("Opening main menu!")
                self.client.release_controls()
                self.client.push_state("WorldMenuState")
                return

        # map may not have a player registered
        if self.player is None:
            return

        if event.button == intentions.INTERACT:
            if event.pressed:
                multiplayer = False
                if multiplayer:
                    self.check_interactable_space()
                    return

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
                return
            elif not event.pressed:
                if direction == self.wants_to_move_player:
                    self.stop_player()
                    return

        if prepare.DEV_TOOLS:
            if event.pressed and event.button == intentions.NOCLIP:
                self.player.ignore_collisions = not self.player.ignore_collisions
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

        # temporary
        if self.current_map.renderer is None:
            self.current_map.initialize_renderer()

        # get player coords to center map
        cx, cy = nearest(self.project(self.player.tile_pos))

        # offset center point for player sprite
        cx += prepare.TILE_SIZE[0] // 2
        cy += prepare.TILE_SIZE[1] // 2

        # center the map on center of player sprite
        # must center map before getting sprite coordinates
        self.current_map.renderer.center((cx, cy))

        # get npc surfaces/sprites
        for npc in self.npcs:
            world_surfaces.extend(self.npcs[npc].get_sprites(self.current_map.sprite_layer))

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
        self.rect = self.current_map.renderer.draw(surface, surface.get_rect(), screen_surfaces)

        # If we want to draw the collision map for debug purposes
        if prepare.CONFIG.collision_map:
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
        self.player = player
        self.add_entity(player)

    def add_entity(self, entity):
        """

        :type entity: tuxemon.core.entity.Entity
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
            return [tuple(dirs2[tile["continue"]] + position)]
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

        # if there are explicit way to exit this position use that information,
        # handles 'continue' and 'exits'
        tile_data = collision_map.get(position)
        if tile_data:
            exits = self.get_explicit_tile_exits(position, tile_data, skip_nodes)
        else:
            exits = None

        # get exits by checking surrounding tiles
        adjacent_tiles = list()
        for direction, neighbor in (
                ("down", (position[0], position[1] + 1)),
                ("right", (position[0] + 1, position[1])),
                ("up", (position[0], position[1] - 1)),
                ("left", (position[0] - 1, position[1])),
        ):
            # if exits are defined make sure the neighbor is present there
            if exits and not neighbor in exits:
                continue

            # check if the neighbor region is present in skipped nodes
            if neighbor in skip_nodes:
                continue

            # We only need to check the perimeter,
            # as there is no way to get further out of bounds
            if neighbor[0] in self.invalid_x or neighbor[1] in self.invalid_y:
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
                    if pairs[direction] not in tile_data["enter"]:
                        continue
                except KeyError:
                    continue

            # no tile data, so assume it is free to move into
            adjacent_tiles.append(neighbor)

        return adjacent_tiles

    ####################################################
    #                Player Movement                   #
    ####################################################
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

    def stop_player(self):
        """ Reset controls and stop player movement at once.  Do not lock controls

        Movement is gracefully stopped.  If player was in a movement, then
        complete it before stopping.

        :return:
        """
        self.wants_to_move_player = None
        self.client.release_controls()
        self.player.cancel_movement()

    def stop_and_reset_player(self):
        """ Reset controls, stop player and abort movement.  Do not lock controls.

        Movement is aborted here, so the player will not complete movement
        to a tile.  It will be reset to the tile where movement started.

        Use if you don't want to trigger another tile event.

        :return:
        """
        self.wants_to_move_player = None
        self.client.release_controls()
        self.player.abort_movement()

    def move_player(self, direction):
        """ Move player in a direction.  Changes facing.

        :param direction:
        :return:
        """
        self.player.move_direction = direction

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

    def move_npcs(self, time_delta):
        """ Move NPCs and Players around according to their state

        :type time_delta: float
        :return:
        """
        # TODO: This function may be moved to a server
        # Draw any game NPC's
        for entity in self.get_all_entities():
            entity.move(time_delta)

            if entity.update_location:
                char_dict = {"tile_pos": entity.final_move_dest}
                networking.update_client(entity, char_dict, self.client)
                entity.update_location = False

        # Move any multiplayer characters that are off map so we know where they should be when we change maps.
        for entity in self.npcs_off_map.values():
            entity.move(time_delta, self)

    def _collision_box_to_pgrect(self, box):
        """Returns a Rect (in screen-coords) version of a collision box (in world-coords).
        """

        # For readability
        x, y = self.get_pos_from_tilepos(box)
        tw, th = self.tile_size

        return Rect(x, y, tw, th)

    def _npc_to_pgrect(self, npc):
        """Returns a Rect (in screen-coords) version of an NPC's bounding box.
        """
        pos = self.get_pos_from_tilepos(npc.tile_pos)
        return Rect(pos, self.tile_size)

    ####################################################
    #                Debug Drawing                     #
    ####################################################
    def debug_drawing(self, surface):
        from pygame.gfxdraw import box

        surface.lock()

        # draw events
        for event in self.client.events:
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

        NOTE: BROKEN

        :param surface: surface to draw on

        :rtype: None
        :returns: None

        """
        raise RuntimeError("deprecated.  refactor!")

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
        logger.debug("Map was not preloaded. Loading from disk.")
        map_data = self.load_map(map_name)

        self.current_map = map_data
        self.collision_map = map_data.collision_map
        self.collision_lines_map = map_data.collision_lines_map
        self.map_size = map_data.size

        # The first coordinates that are out of bounds.
        self.invalid_x = (-1, self.map_size[0])
        self.invalid_y = (-1, self.map_size[1])

        self.client.load_map(map_data)

        # Clear out any existing NPCs
        self.npcs = {}
        self.npcs_off_map = {}
        self.add_player(local_session.player)

        # reset controls and stop moving to prevent player from
        # moving after the teleport and being out of game
        self.stop_player()

        # move to spawn position, if any
        for eo in self.client.events:
            if eo.name.lower() == "player spawn":
                self.player.set_position((eo.x, eo.y))

    def load_map(self, map_name):
        """ Returns map data as a dictionary to be used for map changing
        :rtype: tuxemon.core.map.TuxemonMap
        """
        return TMXMapLoader().load(map_name)

    def check_interactable_space(self):
        """Checks to see if any Npc objects around the player are interactable. It then populates a menu
        of possible actions.

        :param: None

        :rtype: Bool
        :returns: True if there is an Npc to interact with.

        """
        collision_dict = self.player.get_collision_map(self)
        player_tile_pos = nearest(self.player.tile_pos)
        collisions = self.player.collision_check(player_tile_pos, collision_dict, self.collision_lines_map)
        if not collisions:
            pass
        else:
            for direction in collisions:
                if self.player.facing == direction:
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
                            self.client.push_state("InteractionMenu")
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
        networking.update_client(target, event_data["char_dict"], self.client)
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
                        world = self.client.current_state
                        pd = local_session.player.__dict__
                        event_data = {"type": "CLIENT_INTERACTION",
                                      "interaction": "START_DUEL",
                                      "target": [event_data["target"]],
                                      "response": None,
                                      "char_dict": {"monsters": pd["monsters"],
                                                    "inventory": pd["inventory"]
                                                    }

                                      }
                        self.client.server.notify_client_interaction(cuuid, event_data)
