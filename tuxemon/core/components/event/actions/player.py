#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
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
#

import logging
import pygame

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Player(object):

    def teleport(self, game, action):
        """Teleport the player to a particular map and coordinates

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.tools.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: map_name,coordinate_x,coordinate_y

        **Examples:**

        >>> action
        ('teleport', 'pallet_town-room.tmx,5,5', '1', 1)

        """
        prepare = game.imports["prepare"]
        item = game.imports["item"]
        monster = game.imports["monster"]
        Map = game.imports["map"].Map


        # Get the player object from the game.
        player = game.player1
        world = game.state_dict["WORLD"]

        # Get the teleport parameters for the position x,y and the map to load.
        parameters = action[1].split(",")
        mapname = str(parameters[0])
        position_x = int(parameters[1])
        position_y = int(parameters[2])

        # If we're doing a screen transition with this teleport, set the map name that we'll
        # load during the apex of the transition.
        if world.start_transition:
            world.delayed_mapname = mapname

        # Check to see if we're also performing a transition. If we are, wait to perform the
        # teleport at the apex of the transition
        if world.start_transition:
            world.delayed_teleport = True
            # Set the global_x/y variables based on the player's pixel position and the tile size.
            world.delayed_x = player.position[0] - (position_x * player.tile_size[0])
            world.delayed_y = player.position[1] - (position_y * player.tile_size[1]) + player.tile_size[1]
        # If we're not doing a transition, then just do the teleport
        else:
            # Set the global_x/y variables based on the player's pixel position and the tile size.
            world.global_x = player.position[0] - (position_x * player.tile_size[0])
            world.global_y = player.position[1] - (position_y * player.tile_size[1]) + player.tile_size[1]

            ### THIS NEEDS TO BE MOVED IN ITS OWN FUNCTION AND IS DUPLICATED IN THE WORLD STATE ###
            if prepare.BASEDIR + "resources/maps/" + mapname != world.current_map.filename:
                world.current_map = Map(
                    prepare.BASEDIR + "resources/maps/" + mapname)
                world.event_engine.current_map = Map(
                    prepare.BASEDIR + "resources/maps/" + mapname)
                world.tiles, world.collision_map, world.collision_lines_map, world.map_size = world.current_map.loadfile(
                    world.tile_size)
                world.game.events = world.current_map.events

                # Clear out any existing NPCs
                world.npcs = []

                # Scale the loaded tiles if enabled
                if world.scale > 1:
                    x_pos = 0        # Here we need to keep track of the x index of the list
                    # Loop through each row in the map. Each row is a list of
                    # Tile objects in that row.
                    for row in world.tiles:
                        y_pos = 0       # Here we need to keep track of the y index of the list within the row
                        # Now loop through each tile in the row and scale it
                        # accordingly.
                        for column in row:
                            if column:
                                layer_pos = 0
                                for tile in column:
                                    tile["surface"] = pygame.transform.scale(
                                        tile["surface"], (world.tile_size[0], world.tile_size[1]))
                                    world.tiles[x_pos][y_pos][layer_pos] = tile
                                    layer_pos += 1
                            y_pos += 1
                        x_pos += 1
        
        # Update the server/clients of our new map and populate any other players.
        if game.isclient or game.ishost:
            game.add_clients_to_map(game.client.client.registry)
            game.client.update_player(player.facing)
            
        # Stop the player's movement so they don't continue their move after they teleported.
        player.moving = False

    def transition_teleport(self, game, action):
        """Combines the "teleport" and "screen_transition" actions to perform a teleport with a
        screen transition. Useful for allowing the player to go to different maps.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.tools.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: map_name,coordinate_x,coordinate_y,transition_time_in_seconds

        **Examples:**

        >>> action
        ('teleport', 'pallet_town-room.tmx,5,5,2,2', '1', 1)

        """
        # Get the teleport parameters for the position x,y and the map to load.
        parameters = action[1].split(",")
        mapname = parameters[0]
        position_x = parameters[1]
        position_y = parameters[2]
        transition_time = parameters[3]

        # Start the screen transition
        screen_transition = game.event_engine.actions["screen_transition"]["method"]
        transition_action = (action[0], transition_time)
        screen_transition(game, transition_action)

        # Start the teleport. The teleport action will notice a screen transition in progress,
        # and wait until it is done before teleporting.
        teleport_action = (action[0], action[1])
        self.teleport(game, action)


    def add_monster(self, game, action):
        """Adds a monster to the current player's party if there is room. The action parameter
        must contain a monster name to look up in the monster database.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.tools.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: monster_name

        **Example:**

        >>> action
        ... (u'add_monster', u'Bulbatux', 1, 9)
        ...
        >>> monster = core.components.monster.Monster()
        >>> monster.load_from_db(action[1])
        ...
        >>> pprint.pprint(monster.__dict__)
        ... {'attack': 50,
        ...  'attack_modifier': [u'1', u'1.1', u'1.2'],
        ...  'back_battle_sprite': u'resources/gfx/sprites/battle/bulbatux-back.png',
        ...  'body': <core.components.fusion.Body instance at 0x2d0b3f8>,
        ...  'defense': 7,
        ...  'defense_modifier': [u'1', u'1.1', u'1.2'],
        ...  'front_battle_sprite': u'resources/gfx/sprites/battle/bulbatux-front.png',
        ...  'hp': 30,
        ...  'hp_modifier': [u'0.9', u'1', u'1.1'],
        ...  'level': 0,
        ...  'menu_sprite': u'resources/gfx/sprites/battle/bulbatux-menu01.png',
        ...  'monster_id': 1,
        ...  'moves': [],
        ...  'name': u'Bulbatux',
        ...  'special_attack': 9,
        ...  'special_attack_modifier': [u'1', u'1.1', u'1.2'],
        ...  'special_defense': 8,
        ...  'special_defense_modifier': [u'1', u'1.1', u'1.2'],
        ...  'speed': 7,
        ...  'speed_modifier': [u'1', u'1.1', u'1.2'],
        ...  'status': 'Normal',
        ...  'type1': u'grass',
        ...  'type2': u'poison'}
        ...
        >>> game.player1.add_monster(monster)
        >>> game.player1.monsters
        ... [<core.components.monster.Monster instance at 0x2d0b3b0>]

        """

        monster = game.imports["monster"]

        parameters = action[1].split(",")
        monster_name = parameters[0]
        monster_level = parameters[1]
        current_monster = monster.Monster()
        current_monster.load_from_db(monster_name)
        current_monster.set_level(int(monster_level))

        game.player1.add_monster(current_monster)


    def add_item(self, game, action):
        """Adds an item to the current player's inventory. The action parameter must contain an
        item name to look up in the item database.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.tools.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        **Example:**

        >>> action
        ... (u'add_item', u'Potion', 1, 9)
        ...
        >>>

        """

        item = game.imports["item"]

        player = game.player1
        item_to_add = item.Item(action[1])

        # If the item already exists in the player's inventory, add to its quantity, otherwise
        # just add the item.
        if item_to_add.name in player.inventory:
            player.inventory[item_to_add.name]['quantity'] += 1
        else:
            player.inventory[item_to_add.name] = {'item': item_to_add, 'quantity': 1}


    def player_face(self, game, action):
        """Makes the player face a certain direction.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.tools.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: direction

        Action parameter can be: "left", "right", "up", or "down"
        """

        # Get the parameters to determine what direction the player will face.
        parameters = action[1]

        # If we're doing a transition, only change the player's facing when we've reached the apex
        # of the transition.
        if game.state_dict["WORLD"].start_transition:
            game.state_dict["WORLD"].delayed_facing = parameters
        else:
            game.player1.facing = parameters

