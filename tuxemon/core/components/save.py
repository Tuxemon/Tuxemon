#!/usr/bin/python
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
#
#
# core.components.save Handle save games.
#
#

import json
import datetime
import logging
import os
import shelve
from pprint import pformat

import pygame

from core import prepare
from core import tools
from core.components.item import Item
from core.components.monster import Monster
from core.components.technique import Technique

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


def save(player, screenshot, slot, game):
    """Saves the current game state to a file using shelve.

    :param player: The player object that contains data to save.
    :param slot: The save slot to save the data to.
    :param game: The core.control.Control object that runs the game.

    :type player: core.components.player.Player
    :type slot: Integer
    :type game: core.control.Control

    :rtype: None
    :returns: None

    **Examples:**

    >>> core.components.save.save(player1, 2, self)

    """
    # Save a screenshot of the current frame
    pygame.image.save(screenshot, prepare.SAVE_PATH + str(slot) + '.png')
    save_file = open(prepare.SAVE_PATH + str(slot) + '.save', 'w')
    json_data = dict()

    tempinv1 = dict()
    for name,itm in player.inventory.items():
        tempinv1[itm['item'].slug] = itm['quantity']
    json_data["inventory"] = tempinv1

    tempmon1 = list()
    for mon1 in player.monsters:
        tempmon1.append(save_monster(mon1))
    json_data["monsters"] = tempmon1

    tempstorage1 = dict()
    for keysstore, valuesstore in tempstorage1.items():
        if keysstore == 'items':
            tempinv = dict()
            for name,itm in valuesstore.items():
                tempinv[itm['item'].slug] = itm['quantity']
            tempstorage1[keysstore] = tempinv
        if keysstore == 'monsters':
            tempmon = list()
            for monstore in valuesstore:
                tempmon.append(save_monster(monstore))
            tempstorage1[keysstore] = tempmon
    json_data['storage'] = tempstorage1

    json_data['current_map'] = game.get_map_name()
    json_data['game_variables'] = player.game_variables
    json_data['tile_pos'] = player.tile_pos
    json_data['player_name'] = player.name
    json_data['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    json.dump(json_data, save_file)
    save_file.close()
    logger.info("Saving data to save file: " + prepare.SAVE_PATH + str(slot) + '.save')

def save_monster(mon):
    """Prepares a dictionary of the monster to be saved to a file

    :param: None

    :rtype: Dictionary
    :returns: Dictionary containing all the information about the monster

    """
    save_data = dict()
    for key,value in mon.__dict__.items():
        if key == "moves":
            save_data["moves"] = [i.slug for i in mon.moves]
        elif key == "body":
            save_data[key] = save_body(mon.body)
        elif key != "sprites" and key != "moveset" and key != "ai":
            save_data[key] = value
    return save_data

def save_body(body):
    """Prepares a dictionary of the body to be saved to a file

    :param: None

    :rtype: Dictionary
    :returns: Dictionary containing all the information about the body

    """
    save_data = dict(body.__dict__)
    return save_data

def load(slot):
    """Loads game state data from a shelved save file.

    :param slot: The save slot to load game data from.
    :type slot: Integer

    :rtype: Dictionary
    :returns: Dictionary containing game data to load.

    **Examples:**

    >>> core.components.load.load(1)

    """

    # this check is required since opening a shelve will
    # create the pickle is it doesn't already exist.
    # this check prevents a bug where saves are not recorded
    # properly.
    save_path = prepare.SAVE_PATH + str(slot) + '.save'
    if not os.path.exists(save_path):
        return

    saveData = dict()
    with open(save_path, 'r') as save_file:
        json_data = json.load(save_file)
        tempinv = dict()

        for slug,quant in json_data['inventory'].items():
            tempinv1 = dict()
            tempinv1['item'] = Item(slug)
            tempinv1['quantity'] = quant
            tempinv[tempinv1['item'].slug] = tempinv1
        saveData['inventory'] = tempinv

        tempmon = list()
        for mon in json_data['monsters']:
            tempmon1 = Monster()
            tempmon1.load_from_db(mon['slug'])
            load_monster(tempmon1, mon);
            tempmon.append(tempmon1)
        saveData['monsters'] = tempmon

        # TODO: unify loading and game instancing
        # Loop through the storage item keys and re-add the surface.
        tempstorage = dict()
        for keys, values in json_data['storage'].items():
            if keys == 'items':
                tempinv = dict()

                for slug,quant in values.items():
                    tempinv1 = dict()
                    tempinv1['item'] = Item(slug)
                    tempinv1['quantity'] = quant
                    tempinv[tempinv1['item'].slug] = tempinv1
                tempstorage[keys] = tempinv

            elif keys == 'monsters':
                tempmon = list()
                for mon in values:
                    tempmon1 = Monster()
                    tempmon1.load_from_db(mon['slug'])
                    load_monster(tempmon1, mon);
                    tempmon.append(tempmon1)
                tempstorage[keys] = tempmon
            else:
                tempstorage[keys] = values
        saveData['storage'] = tempstorage

        saveData['game_variables'] = json_data['game_variables']
        saveData['tile_pos'] = json_data['tile_pos']
        saveData['current_map'] = json_data['current_map']
        saveData['player_name'] = json_data['player_name']
        saveData['time'] = json_data['time']

    return saveData

def load_monster(mon, save_data):
    """Loads information from saved data

    :param save_data: Dictionary loaded from the json file

    :rtype: None
    :returns: None

    """
    for key,value in save_data.items():
        if key == "moves":
            mon.moves = [Technique(i) for i in value]
        elif key == "body":
            load_body(mon, value)
        else:
            setattr(mon, key, value)
    mon.load_sprites()

def load_body(body, save_data):
    """Loads information from saved data

    :param save_data: Dictionary loaded from the json file

    :rtype: None
    :returns: None

    """
    for key,value in save_data.items():
        setattr(body, key, value)
