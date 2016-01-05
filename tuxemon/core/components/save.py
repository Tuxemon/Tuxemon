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

import logging
import shelve
import pygame
import datetime
from pprint import pformat
from core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


def save(player, slot, game):
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
    pygame.image.save(game.save_screenshot, prepare.SAVE_PATH + str(slot) + '.png')
    saveFile = shelve.open(prepare.SAVE_PATH + str(slot) + '.save')
    saveFile['game_variables'] = game.player1.game_variables
    saveFile['tile_pos'] = game.player1.tile_pos
    tempinv1 = {}
    tempinv1 = dict(game.player1.inventory)
    for keysinv, valuesinv in tempinv1.items():
        for keys2inv, values2inv in valuesinv.items():
            if keys2inv == 'item':
                values2inv.surface = None
    saveFile['inventory'] = tempinv1
    saveFile['current_map'] = game.event_engine.current_map.filename.split("/")[-1]
    tempmon1 = []
    tempmon1 = list(game.player1.monsters)
    for mon1 in tempmon1:
        if mon1.sprites:
            mon1.sprites = {}
    saveFile['monsters'] = tempmon1
    tempstorage1 = {}
    tempstorage1 = dict(game.player1.storage)
    for keysstore, valuesstore in tempstorage1.items():
        if keysstore == 'items':
            for keys2store, values2store in valuesstore.items():
                for keys3store, values3store in values2store.items():
                    if keys3store == 'item':
                        values3store.surface = None
        if keysstore == 'monsters':
            for monstore in valuesstore:
                monstore.sprites = {}
    saveFile['storage'] = tempstorage1
    saveFile['player_name'] = game.player1.name
    saveFile['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    logger.info("Saving data to save file: " + pformat(saveFile))
    saveFile.close()


def load(slot):
    """Loads game state data from a shelved save file.

    :param slot: The save slot to load game data from.
    :type slot: Integer

    :rtype: Dictionary
    :returns: Dictionary containing game data to load.

    **Examples:**

    >>> core.components.save.load(1)

    """

    saveFile = shelve.open(prepare.SAVE_PATH + str(slot) + '.save')
    saveData = {}

    saveData['game_variables'] = saveFile['game_variables']
    saveData['tile_pos'] = saveFile['tile_pos']
    tempinv = {}
    tempinv = dict(saveFile['inventory'])
    for keys, values in tempinv.items():
        for keys2, values2 in values.items():
            if keys2 == 'item':
                values2.surface = pygame.image.load(prepare.BASEDIR +
                                                    values2.sprite
                                                    ).convert_alpha()
    saveData['inventory'] = tempinv
    tempmon = []
    tempmon = list(saveFile['monsters'])
    for mon in tempmon:
        mon.load_sprites(prepare.SCALE)
    saveData['monsters'] = tempmon
    tempstorage = {}
    # Loop through the storage item keys and re-add the surface.
    tempstorage = dict(saveFile['storage'])
    for keys, values in tempstorage.items():
        if keys == 'items':
            for keys2, values2 in values.items():
                for keys3, values3 in values2.items():
                    if keys3 == 'item':
                        values3.surface = pygame.image.load(prepare.BASEDIR +
                                                            values3.sprite
                                                            ).convert_alpha()
        if keys == 'monsters':
            for storemon1 in values:
                storemon1.load_sprites(prepare.SCALE)
    saveData['storage'] = tempstorage
    saveData['current_map'] = saveFile['current_map']
    saveData['player_name'] = saveFile['player_name']
    saveData['time'] = saveFile['time']

    return saveData
