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
# Derek Clark <derekjohn.clark@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
#
# core.npc
#

import logging
import os
from math import hypot

from tuxemon.compat import Rect
from tuxemon.core import pyganim
from tuxemon.core.db import db
from tuxemon.core.entity import Entity
from tuxemon.core.item.item import Item
from tuxemon.core.item.item import decode_inventory, encode_inventory
from tuxemon.core.locale import T
from tuxemon.core.map import proj, facing, dirs3, dirs2, get_direction
from tuxemon.core.monster import Monster, MAX_LEVEL, decode_monsters, encode_monsters
from tuxemon.core.prepare import CONFIG
from tuxemon.core.tools import nearest, trunc
from tuxemon.core.graphics import load_and_scale

logger = logging.getLogger(__name__)

# reference direction and movement states to animation names
# this dictionary is kinda wip, idk
animation_mapping = {
    True: {
        'up': 'back_walk',
        'down': 'front_walk',
        'left': 'left_walk',
        'right': 'right_walk'},
    False: {
        'up': 'back',
        'down': 'front',
        'left': 'left',
        'right': 'right'}
}


def tile_distance(tile0, tile1):
    x0, y0 = tile0
    x1, y1 = tile1
    return hypot(x1 - x0, y1 - y0)


class NPC(Entity):
    """ Class for humanoid type game objects, NPC, Players, etc

    Currently, all movement is handled by a queue called "path".  This queue
    provides robust movement in a tile based environment.  It supports arbitrary
    length paths for directly setting a series of movements.

    Pathfinding is accomplished by setting the path directly.

    To move one tile, simply set a path of one item.
    """
    party_limit = 6  # The maximum number of tuxemon this npc can hold

    def __init__(self, npc_slug, sprite_name=None,combat_front=None,combat_back=None):
        super().__init__()

        # load initial data from the npc database
        npc_data = db.lookup(npc_slug, table="npc")

        self.slug = npc_slug

        # This is the NPC's name to be used in dialog
        self.name = T.translate(self.slug)

        # use 'animations' passed in
        # Hold on the the string so it can be sent over the network
        self.sprite_name = sprite_name
        self.combat_front = combat_front
        self.combat_back = combat_back
        if self.sprite_name is None:
            # Try to use the sprites defined in the JSON data
            self.sprite_name = npc_data["sprite_name"]
        if self.combat_front is None:
            self.combat_front = npc_data["combat_front"]
        if self.combat_back is None:
            self.combat_back = npc_data["combat_back"]

        # general
        self.behavior = "wander"  # not used for now
        self.game_variables = {}  # Tracks the game state
        self.interactions = []  # List of ways player can interact with the Npc
        self.isplayer = False  # used for various tests, idk
        self.monsters = []  # This is a list of tuxemon the npc has. Do not modify directly
        self.inventory = {}  # The Player's inventory.
        self.storage = {"monsters": [], "items": {}}

        # combat related
        self.ai = None  # Whether or not this player has AI associated with it
        self.speed = 10  # To determine combat order (not related to movement!)
        self.moves = []  # list of techniques

        # pathfinding and waypoint related
        self.pathfinding = None
        self.path = []
        self.final_move_dest = [0, 0]  # Stores the final destination sent from a client

        # This is used to 'set back' when lost, and make movement robust.
        # If entity falls off of map due to a bug, it can be returned to this value.
        # When moving to a waypoint, this is used to detect if movement has overshot
        # the destination due to speed issues or framerate jitters.
        self.path_origin = None

        # movement related
        self.move_direction = None  # Set this value to move the npc (see below)
        self.facing = "down"  # Set this value to change the facing direction
        self.moverate = CONFIG.player_walkrate  # walk by default
        self.ignore_collisions = False

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction until it is set to None.

        # TODO: move sprites into renderer so class can be used headless
        self.playerHeight = 0
        self.playerWidth = 0
        self.standing = {}  # Standing animation frames
        self.sprite = {}  # Moving animation frames
        self.moveConductor = pyganim.PygConductor()
        self.load_sprites()
        self.rect = Rect(self.tile_pos, (self.playerWidth, self.playerHeight))  # Collision rect

    def get_state(self, session):
        """Prepares a dictionary of the npc to be saved to a file

        :param tuxemon.core.session.Session session:

        :rtype: Dictionary
        :returns: Dictionary containing all the information about the npc

        """
        return {
            'current_map': session.client.get_map_name(),
            'facing': self.facing,
            'game_variables': self.game_variables,
            'inventory': encode_inventory(self.inventory),
            'monsters': encode_monsters(self.monsters),
            'player_name': self.name,
            'storage': {
                'items': encode_inventory(self.storage['items']),
                'monsters': encode_monsters(self.storage['monsters']),
            },
            'tile_pos': nearest(self.tile_pos),
        }

    def set_state(self, session,  save_data):
        """Recreates npc from saved data

        :param tuxemon.core.session.Session session:
        :param Dict save_data: Data used to recreate the player

        :rtype: None
        :returns: None

        """

        self.facing = save_data.get('facing', 'down')
        self.game_variables = save_data['game_variables']
        self.inventory = decode_inventory(session, self, save_data)
        self.monsters = decode_monsters(save_data)
        self.name = save_data['player_name']
        self.storage = {
            'items': decode_inventory(session, self, save_data['storage']),
            'monsters': decode_monsters(save_data['storage']),
        }

    def load_sprites(self):
        """ Load sprite graphics

        :return:
        """
        # TODO: refactor animations into renderer
        # Get all of the player's standing animation images.
        self.standing = {}
        for standing_type in facing:
            filename = "{}_{}.png".format(self.sprite_name, standing_type)
            path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)

        self.playerWidth, self.playerHeight = self.standing["front"].get_size()  # The player's sprite size in pixels

        # avoid cutoff frames when steps don't line up with tile movement
        frames = 3
        frame_duration = (1000 / CONFIG.player_walkrate) / frames / 1000 * 2

        # Load all of the player's sprite animations
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images = [
                'sprites/{}_{}.{}.png'.format(
                    self.sprite_name,
                    anim_type,
                    str(num).rjust(3, '0')
                )
                for num in range(4)
            ]

            frames = []
            for image in images:
                surface = load_and_scale(image)
                frames.append((surface, frame_duration))

            self.sprite[anim_type] = pyganim.PygAnimation(frames, loop=True)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animation objects
        # at the same time, so that way they'll always be in sync with each other.
        self.moveConductor.add(self.sprite)

    def get_sprites(self, layer):
        """ Get the surfaces and layers for the sprite

        Used to render the player

        TODO: Move the 'layer' to the NPC class so characters
        can define their own drawing layer.

        :param layer: The layer to draw the sprite on.
        :type layer: Int

        :return:
        """

        def get_frame(d, ani):
            frame = d[ani]
            try:
                surface = frame.getCurrentFrame()
                frame.rate = self.moverate / CONFIG.player_walkrate
                return surface
            except AttributeError:
                return frame

        # TODO: move out to the world renderer
        frame_dict = self.sprite if self.moving else self.standing
        state = animation_mapping[self.moving][self.facing]
        return [(get_frame(frame_dict, state), self.tile_pos, layer)]

    def pathfind(self, destination):
        """ Find a path and also start it

        Queries the world for a valid path

        :param destination:
        :return:
        """
        # TODO: handle invalid paths
        self.pathfinding = destination
        path = self.world.pathfind(tuple(self.tile_pos), destination)
        if path:
            self.path = path
            self.next_waypoint()

    def check_continue(self):
        try:
            pos = tuple(int(i) for i in self.tile_pos)
            direction_next = self.world.collision_map[pos]["continue"]
            self.move_one_tile(direction_next)
        except (KeyError, TypeError):
            pass

    def stop_moving(self):
        """ Completely stop all movement

        Be careful, if stopped while in the path, it might not be tile-aligned.

        May continue if move_direction is set

        :return: None
        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def cancel_path(self):
        """ Stop following a path.

        NPC may still continue to move if move_direction has been set

        :return:
        """
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self):
        """ Gracefully stop moving.  If in a path, then will finish tile movement.

        Generally, use this if you want to stop.  Will stop at a tile coord.

        :return:
        """
        self.move_direction = None
        if self.tile_pos == self.path_origin:
            # we *just* started a new path; discard it and stop
            self.abort_movement()
        elif self.path and self.moving:
            # we are in the middle of moving between tiles
            self.path = [self.path[-1]]
            self.pathfinding = None
        else:
            # probably already stopped, just clear the path
            self.stop_moving()
            self.cancel_path()

    def abort_movement(self):
        """ Stop moving, cancel paths, and reset tile position to center

        The tile postion will be truncated, so even if there is another
        closer tile, it will always return the the tile where movement
        started.

        This is a useful method if you want to abort a path movement
        and also don't want to advance to another tile.

        :return:
        """
        if self.path_origin is not None:
            self.tile_pos = tuple(self.path_origin)
        self.move_direction = None
        self.stop_moving()
        self.cancel_path()

    def move(self, time_passed_seconds):
        """ Move the entity around the game world

        * check if the move_direction variable is set
        * set the movement speed
        * follow waypoints
        * control walking animations
        * send network updates

        :param time_passed_seconds: A float of the time that has passed since the last frame.
            This is generated by clock.tick() / 1000.0.

        :type time_passed_seconds: Float
        """
        # update physics.  eventually move to another class
        self.update_physics(time_passed_seconds)

        if self.pathfinding and not self.path:
            # wants to pathfind, but there was no path last check
            self.pathfind(self.pathfinding)

        if self.path:
            if self.path_origin:
                # if path origin is set, then npc has started moving
                # from one tile to another.
                self.check_waypoint()
            else:
                # if path origin is not set, then a previous attempt to change
                # waypoints failed, so try again.
                self.next_waypoint()

        # does the npc want to move?
        if self.move_direction:
            if self.path and not self.moving:
                # npc wants to move and has a path, but it is blocked
                self.cancel_path()

            if not self.path:
                # there is no path, so start a new one
                self.move_one_tile(self.move_direction)
                self.next_waypoint()

        # TODO: determine way to tell if another force is moving the entity
        # TODO: basically, this simple check will only allow explicit npc movement
        # TODO: its not possible to move the entity with physics b/c this stops that
        if not self.path:
            self.cancel_movement()
            self.moveConductor.stop()

    def move_one_tile(self, direction):
        """ Ask entity to move one tile

        :type direction: str
        :param direction: up, down, left right

        :return: None
        """
        self.path.append(trunc(self.tile_pos + dirs2[direction]))

    def valid_movement(self, tile):
        """ Check the game map to determine if a tile can be moved into

        * Only checks adjacent tiles
        * Uses all advanced tile movements, like continue tiles

        :param tile:
        :return:
        """
        return tile in self.world.get_exits(trunc(self.tile_pos)) or self.ignore_collisions

    @property
    def move_destination(self):
        """ Only used for the player_moved condition.

        :return:
        """
        if self.path:
            return self.path[-1]
        else:
            return None

    def next_waypoint(self):
        """ Take the next step of the path, stop if way is blocked

        * This must be called after a path is set
        * Not needed to be called if existing path is modified
        * If the next waypoint is blocked, the waypoint will be removed

        :return: None
        """
        target = self.path[-1]
        direction = get_direction(self.tile_pos, target)
        self.facing = direction
        if self.valid_movement(target):
            # pyganim has horrible clock drift.  even after one animation
            # cycle, the time will be off.  drift causes the walking steps to not
            # align with tiles and some frames will only last one game frame.
            # using play to start each tile will reset the pyganim timer
            # and prevent the walking animation frames from coming out of sync.
            # it still occasionally happens though!
            # eventually, there will need to be a global clock for the game,
            # not based on wall time, to prevent visual glitches.
            self.moveConductor.play()
            self.path_origin = tuple(self.tile_pos)
            self.velocity3 = self.moverate * dirs3[direction]
        else:
            # the target is blocked now
            self.stop_moving()

            if self.pathfinding:
                # since we are pathfinding, just try a new path
                logger.error('{} finding new path!'.format(self.slug))
                self.pathfind(self.pathfinding)

            else:
                # give up and wait until the target is clear again
                pass

    def check_waypoint(self):
        """ Check if the waypoint is reached and sets new waypoint if so

        * For most accurate speed, tests distance traveled.
        * Doesn't verify the target position, just distance
        * Assumes once waypoint is set, direction doesn't change
        * Honors continue tiles

        :return: None
        """
        target = self.path[-1]
        expected = tile_distance(self.path_origin, target)
        traveled = tile_distance(self.tile_pos, self.path_origin)
        if traveled >= expected:
            self.set_position(target)
            self.path.pop()
            self.path_origin = None
            self.check_continue()  # handle "continue" tiles
            if self.path:
                self.next_waypoint()

    def pos_update(self):
        """ WIP.  Required to be called after position changes

        :return:
        """
        self.tile_pos = proj(self.position3)
        self.network_notify_location_change()

    def network_notify_start_moving(self, direction):
        r""" WIP guesswork ¯\_(ツ)_/¯

        :return:
        """
        if self.world.game.isclient or self.world.game.ishost:
            self.world.game.client.update_player(direction, event_type="CLIENT_MOVE_START")

    def network_notify_stop_moving(self):
        r""" WIP guesswork ¯\_(ツ)_/¯

        :return:
        """
        if self.world.game.isclient or self.world.game.ishost:
            self.world.game.client.update_player(self.facing, event_type="CLIENT_MOVE_COMPLETE")

    def network_notify_location_change(self):
        r""" WIP guesswork ¯\_(ツ)_/¯

        :return:
        """
        self.update_location = True

    ####################################################
    #                   Monsters                       #
    ####################################################
    def add_monster(self, monster):
        """Adds a monster to the player's list of monsters. If the player's party is full, it
        will send the monster to PCState archive.

        :param monster: The core.monster.Monster object to add to the player's party.

        :type monster: tuxemon.core.monster.Monster

        :rtype: None
        :returns: None

        """
        monster.owner = self
        if len(self.monsters) >= self.party_limit:
            self.storage["monsters"].append(monster)
        else:
            self.monsters.append(monster)
            self.set_party_status()

    def find_monster(self, monster_slug):
        """Finds a monster in the player's list of monsters.

        :param monster_slug: The slug name of the monster
        :type monster_slug: str

        :rtype: tuxemon.core.monster.Monster
        :returns: Monster found
        """
        for monster in self.monsters:
            if monster.slug == monster_slug:
                return monster

    def remove_monster(self, monster):
        """ Removes a monster from this player's party.

        :param monster: Monster to remove from the player's party.

        :type monster: tuxemon.core.monster.Monster

        :rtype: None
        :returns: None
        """
        if monster in self.monsters:
            monster.owner = None
            self.monsters.remove(monster)
            self.set_party_status()

    def switch_monsters(self, index_1, index_2):
        """ Swap two monsters in this player's party

        :param index_1/index_2: The indexes of the monsters to switch in the player's party.

        :type index_1: int
        :type index_2: int

        :rtype: None
        :returns: None
        """
        self.monsters[index_1], self.monsters[index_2] = self.monsters[index_2], self.monsters[index_1]

    def load_party(self):
        """ Loads the party of this npc from their npc.json entry.

        :rtype: None
        :returns: None
        """
        for monster in self.monsters:
            self.remove_monster(monster)

        self.monsters = []

        # Look up the NPC's details from our NPC database
        npc_details = db.database['npc'][self.slug]
        for npc_monster_details in npc_details['monsters']:
            monster = Monster(save_data=npc_monster_details)
            monster.experience_give_modifier = npc_monster_details['exp_give_mod']
            monster.experience_required_modifier = npc_monster_details['exp_req_mod']
            monster.set_level(monster.level)
            monster.current_hp = monster.hp

            # Add our monster to the NPC's party
            self.add_monster(monster)

    def set_party_status(self):
        """ Records important information about all monsters in the party.

        :rtype: None
        :returns: None
        """
        if not self.isplayer or len(self.monsters) == 0:
            return

        level_lowest = MAX_LEVEL
        level_highest = 0
        level_average = 0
        for npc_monster in self.monsters:
            if npc_monster.level < level_lowest:
                level_lowest = npc_monster.level
            if npc_monster.level > level_highest:
                level_highest = npc_monster.level
            level_average += npc_monster.level
        level_average = int(round(level_average / len(self.monsters)))
        self.game_variables['party_level_lowest'] = level_lowest
        self.game_variables['party_level_highest'] = level_highest
        self.game_variables['party_level_average'] = level_average

    def give_item(self, session,  target, item, quantity):
        subtract = self.alter_item_quantity(session, item.slug, -quantity)
        give = target.alter_item_quantity(session, item.slug, quantity)
        return subtract and give

    def has_item(self, item_slug):
        return self.inventory.get(item_slug) is not None

    def alter_item_quantity(self, session, item_slug, amount):
        success = True
        item = self.inventory.get(item_slug)
        if amount > 0:
            if item:
                item['quantity'] += amount
            else:
                self.inventory[item_slug] = {
                    'item': Item(session, self, item_slug),
                    'quantity': amount,
                }
        elif amount < 0:
            amount = abs(amount)
            if item is None or item.get('infinite'):
                pass
            elif item['quantity'] == amount:
                del self.inventory[item_slug]
            elif item['quantity'] > amount:
                item['quantity'] -= amount
            else:
                success = False

        return success

    def speed_test(self, action):
        return self.speed
