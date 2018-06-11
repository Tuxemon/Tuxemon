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

import pygame

from tuxemon.core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


def get_save_data(player, game):
    """Gets a dictionary which represents the state of the game.

    :param player: The player object that contains data to save.
    :param game: The core.control.Control object that runs the game.

    :type player: core.components.player.Player
    :type game: core.control.Control

    :rtype: Dictionary
    :returns: Game data to save, must be JSON encodable.

    """
    save_data = player.get_state(game)
    save_data['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return save_data


def save(save_data, screenshot, slot):
    """Saves the current game state to a file using shelve.

    :param save_data: The data to save.
    :param screenshot: An image of the current frame
    :param slot: The save slot to save the data to.

    :type save_data: Dictionary
    :type screenshot: pygame.Image
    :type slot: Integer

    :rtype: None
    :returns: None

    """
    # Save a screenshot of the current frame
    pygame.image.save(screenshot, prepare.SAVE_PATH + str(slot) + '.png')
    save_path = prepare.SAVE_PATH + str(slot) + '.save'
    with open(save_path, 'w') as f:
        logger.info("Saving data to save file: " + save_path)
        json.dump(save_data, f)


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

    with open(save_path, 'r') as save_file:
        return json.load(save_file)
