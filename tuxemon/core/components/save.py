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
import sys
from pprint import pformat

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
    pygame.image.save(game.save_screenshot, 'saves/slot' + str(slot) + '.png')

    saveFile = shelve.open('saves/slot' + str(slot) + '.save')
    saveFile['game_variables'] = game.player1.game_variables
    saveFile['tile_pos'] = game.player1.tile_pos
    saveFile['inventory'] = game.player1.inventory
    saveFile['current_map'] = game.event_engine.current_map.filename
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

    saveFile = shelve.open('saves/slot' + str(slot) + '.save')
    saveData = {}

    saveData['game_variables'] = saveFile['game_variables']
    saveData['tile_pos'] = saveFile['tile_pos']
    saveData['inventory'] = saveFile['inventory']
    saveData['current_map'] = saveFile['current_map']
    saveData['player_name'] = saveFile['player_name']
    saveData['time'] = saveFile['time']

    return saveData


if __name__ == "__main__":
    saveFile = shelve.open('saves/slot2.save')

    # Create save file
    saveFile['game_variables'] = {"battle_won": "yes"}
    saveFile['tile_pos'] = (1,2)
    saveFile['inventory'] = []
    saveFile['current_map'] = "pallet_town-room.map"
    saveFile['player_name'] = "Blue"
    saveFile['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    saveFile.close()

    # Load save file
    print load(1)

    #print player
