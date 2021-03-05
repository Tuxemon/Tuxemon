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
# npc
#

import logging
from math import hypot

from tuxemon.db import db
from tuxemon.entity import Entity
from tuxemon.item.item import Item
from tuxemon.item.item import decode_inventory, encode_inventory
from tuxemon.locale import T
from tuxemon.map import dirs3, dirs2, get_direction
from tuxemon.monster import Monster, MAX_LEVEL, decode_monsters, encode_monsters
from tuxemon.prepare import CONFIG
from tuxemon.tools import nearest, trunc

logger = logging.getLogger(__name__)

# reference direction and movement states to animation names
# this dictionary is kinda wip, idk
animation_mapping = {
    True: {"up": "back_walk", "down": "front_walk", "left": "left_walk", "right": "right_walk"},
    False: {"up": "back", "down": "front", "left": "left", "right": "right"},
}


def tile_distance(tile0, tile1):
    x0, y0 = tile0
    x1, y1 = tile1
    return hypot(x1 - x0, y1 - y0)


class NPC(Entity):
    """Class for humanoid type game objects, NPC, Players, etc

    Currently, all movement is handled by a queue called "path".  This queue
    provides robust movement in a tile based environment.  It supports arbitrary
    length paths for directly setting a series of movements.

    Pathfinding is accomplished by setting the path directly.

    To move one tile, set a path of one item.
    """

    party_limit = 6  # The maximum number of tuxemon this npc can hold

    def __init__(self, npc_slug, sprite_name=None, combat_front=None, combat_back=None):
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
        # Variables for long-term item and monster storage
        # Keeping these seperate so other code can safely
        # assume that all values are lists
        self.monster_boxes = dict()
        self.item_boxes = dict()

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
        self._move_direction = None  # Set this value to move the npc (see below)
        self.facing = "down"  # Set this value to change the facing direction
        self.moverate = CONFIG.player_walkrate  # walk by default
        self.ignore_collisions = False

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction until it is set to None.

        # TODO: pull values from the sprite, json, or some default
        self.playerHeight = 16
        self.playerWidth = 16
        # self.rect = Rect(self.tile_pos, (self.playerWidth, self.playerHeight))  # Collision rect

        self.animation = None

    def get_state(self, session):
        """Prepares a dictionary of the npc to be saved to a file

        :param tuxemon.session.Session session:
        :rtype: Dictionary
        :returns: Dictionary containing all the information about the npc
        """

        state = {
            'current_map': session.client.get_map_name(),
            'facing': self.facing,
            'game_variables': self.game_variables,
            'inventory': encode_inventory(self.inventory),
            'monsters': encode_monsters(self.monsters),
            'player_name': self.name,
            'monster_boxes': dict(),
            'item_boxes': dict(),
            'tile_pos': nearest(self.tile_pos),
        }

        for key, value in self.monster_boxes.items():
            state['monster_boxes'][key] = encode_monsters(value)
        for key, value in self.item_boxes.items():
            state['item_boxes'][key] = encode_inventory(value)

        return state

    def set_state(self, session,  save_data):
        """Recreates npc from saved data

        :param tuxemon.session.Session session:
        :param Dict save_data: Data used to recreate the player
        :rtype: None
        """

        self.facing = save_data.get('facing', 'down')
        self.game_variables = save_data['game_variables']
        self.inventory = decode_inventory(session, self, save_data.get('inventory', {}))
        self.monsters = decode_monsters(save_data.get("monsters"))
        self.name = save_data['player_name']
        for key, value in save_data['monster_boxes'].items():
            self.monster_boxes[key] = decode_monsters(value)
        for key, value in save_data['item_boxes'].items():
            self.item_boxes[key] = decode_inventory(session, self, value)

    def move_direction(self, direction):
        self._move_direction = direction

    def pathfind(self, destination):
        """Find a path and also start it

        :param destination:
        :rtype: None
        """
        self.pathfinding = destination
        path = self.map.pathfind(tuple(self.tile_pos), destination)
        if path:
            self.path = path
            self.next_waypoint()

    def check_continue(self):
        """

        :return:
        """
        try:
            pos = tuple(int(i) for i in self.tile_pos)
            direction_next = self.map.collision_map[pos]["continue"]
            self.move_one_tile(direction_next)
        except (KeyError, TypeError):
            pass

    def cancel_path(self):
        """Stop following a path.

        NPC may still continue to move if move_direction has been set

        :return:
        """
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self):
        """Gracefully stop moving.  If in a path, then will finish tile movement.

        Generally, use this if you want to stop.  Will stop at a tile coord.

        :return:
        """
        self._move_direction = None
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
        """Stop moving, cancel paths, and reset tile position to center

        The tile postion will be truncated, so even if there is another
        closer tile, it will always return the the tile where movement
        started.

        This is a useful method if you want to abort a path movement
        and also don't want to advance to another tile.

        :return:
        """
        if self.path_origin is not None:
            self.tile_pos = tuple(self.path_origin)
        self._move_direction = None
        self.stop_moving()
        self.cancel_path()

    def move(self, time_passed_seconds):
        """Move the entity around the game map

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
            self.pathfind(self.pathfinding)

        if self.path:
            if self.path_origin:
                self.check_waypoint()
            else:
                self.next_waypoint()

        if self._move_direction:
            if self.path and not self.moving:
                # npc wants to move and has a path, but it is blocked
                self.cancel_path()

            if not self.path:
                self.move_one_tile(self._move_direction)
                self.next_waypoint()

        # TODO: determine way to tell if another force is moving the entity
        # TODO: basically, this simple check will only allow explicit npc movement
        # TODO: its not possible to move the entity with physics b/c this stops that
        if not self.path:
            self.cancel_movement()

    def move_one_tile(self, direction):
        """Ask entity to move one tile

        :type direction: str
        :param direction: up, down, left right
        """
        self.path.append(trunc(self.tile_pos + dirs2[direction]))

    def valid_movement(self, tile):
        """Check the game map to determine if a tile can be moved into

        * Only checks adjacent tiles
        * Uses all advanced tile movements, like continue tiles

        :param tile:
        """
        return tile in self.map.get_exits(trunc(self.tile_pos)) or self.ignore_collisions

    @property
    def move_destination(self):
        """Only used for the player_moved condition."""
        if self.path:
            return self.path[-1]
        else:
            return None

    def next_waypoint(self):
        """Take the next step of the path, stop if way is blocked

        * This must be called after a path is set
        * Not needed to be called if existing path is modified
        * If the next waypoint is blocked, the waypoint will be removed
        """
        target = self.path[-1]
        direction = get_direction(self.tile_pos, target)
        self.facing = direction
        if self.valid_movement(target):
            self.path_origin = tuple(self.tile_pos)
            self.velocity3 = self.moverate * dirs3[direction]
        else:
            # the target is blocked now
            self.stop_moving()

            if self.pathfinding:
                # since we are pathfinding, just try a new path
                logger.error(f"{self.slug} finding new path!")
                self.pathfind(self.pathfinding)

            else:
                # give up and wait until the target is clear again
                pass

    def check_waypoint(self):
        """Check if the waypoint is reached and sets new waypoint if so

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

    ####################################################
    #                   Monsters                       #
    ####################################################
    def add_monster(self, monster):
        """Adds a monster to the player's list of monsters. If the player's party is full, it
        will send the monster to PCState archive.

        :param monster: The monster.Monster object to add to the player's party.
        :type monster: tuxemon.monster.Monster
        """
        monster.owner = self
        if len(self.monsters) >= self.party_limit:
            self.monster_boxes[CONFIG.default_monster_storage_box].append(monster)
        else:
            self.monsters.append(monster)
            self.set_party_status()

    def find_monster(self, monster_slug):
        """Finds a monster in the player's list of monsters.

        :param monster_slug: The slug name of the monster
        :type monster_slug: str

        :rtype: tuxemon.monster.Monster
        """
        for monster in self.monsters:
            if monster.slug == monster_slug:
                return monster

    def find_monster_by_id(self, instance_id):
        """Finds a monster in the player's list which has the given instance_id.

        :param instance_id: The instance_id of the monster.
        :type instance_id: uuid.UUID4

        :rtype: tuxemon.core.monster.Monster
        :return: Monster found, or None.

        """
        return next((m for m in self.monsters if m.instance_id == instance_id), None)

    def find_monster_in_storage(self, instance_id):
        """Finds a monster in the player's storage boxes which has the given instance_id.

        :param instance_id: The insance_id of the monster.
        :type instance_id: uuid.UUID4

        :rtype: tuxemon.core.monster.Monster
        :return: Monster found, or None.

        """
        monster = None
        for box in self.monster_boxes.values():
            monster = next((m for m in box if m.instance_id == instance_id), None)
            if monster is not None:
                break

        return monster

    def remove_monster(self, monster):
        """Removes a monster from this player's party.

        :param monster: Monster to remove from the player's party.
        :type monster: tuxemon.monster.Monster
        """
        if monster in self.monsters:
            self.monsters.remove(monster)
            self.set_party_status()

    def remove_monster_from_storage(self, monster):
        """ Removes the monster from the player's storage.

        :param monster: Monster to remove from storage.
        :type monster: tuxemon.core.monster.Monster

        :return: None
        :rtype: None
        """

        for box in self.monster_boxes.values():
            if monster in box:
                box.remove(monster)
                return

    def switch_monsters(self, index_1, index_2):
        """Swap two monsters in this player's party

        :param index_1: The indexes of the monsters to switch in the player's party.
        :param index_2: The indexes of the monsters to switch in the player's party.
        :type index_1: int
        :type index_2: int
        """
        self.monsters[index_1], self.monsters[index_2] = self.monsters[index_2], self.monsters[index_1]

    def load_party(self):
        """Loads the party of this npc from their npc.json entry."""
        for monster in self.monsters:
            self.remove_monster(monster)

        self.monsters = []

        # Look up the NPC's details from our NPC database
        npc_details = db.database["npc"][self.slug]
        for npc_monster_details in npc_details["monsters"]:
            monster = Monster(save_data=npc_monster_details)
            monster.experience_give_modifier = npc_monster_details["exp_give_mod"]
            monster.experience_required_modifier = npc_monster_details["exp_req_mod"]
            monster.set_level(monster.level)
            monster.current_hp = monster.hp

            # Add our monster to the NPC's party
            self.add_monster(monster)

    def set_party_status(self):
        """Records important information about all monsters in the party."""
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
        self.game_variables["party_level_lowest"] = level_lowest
        self.game_variables["party_level_highest"] = level_highest
        self.game_variables["party_level_average"] = level_average

    def give_item(self, session, target, item, quantity):
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
                item["quantity"] += amount
            else:
                self.inventory[item_slug] = {
                    "item": Item(session, self, item_slug),
                    "quantity": amount,
                }
        elif amount < 0:
            amount = abs(amount)
            if item is None or item.get("infinite"):
                pass
            elif item["quantity"] == amount:
                del self.inventory[item_slug]
            elif item["quantity"] > amount:
                item["quantity"] -= amount
            else:
                success = False

        return success

    def speed_test(self, action):
        return self.speed
