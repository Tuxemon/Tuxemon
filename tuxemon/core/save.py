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
# core.save Handle save games.
#
#


import base64
import datetime
import json
import logging
from operator import itemgetter

import pygame

from tuxemon.core import prepare
from tuxemon.core.save_upgrader import SAVE_VERSION, upgrade_save

try:
    import cbor
except ImportError:
    prepare.SAVE_METHOD = "JSON"

logger = logging.getLogger(__name__)

slot_number = None
TIME_FORMAT = "%Y-%m-%d %H:%M"


def get_save_data(session):
    """Gets a dictionary which represents the state of the session.

    :param tuxemon.core.session.Session session: Game session

    :rtype: Dictionary
    :returns: Game data to save, must be JSON encodable.

    """
    save_data = session.player.get_state(session)
    screenshot = capture_screenshot(session.client)
    save_data['screenshot'] = base64.b64encode(pygame.image.tostring(screenshot, "RGB")).decode('utf-8')
    save_data['screenshot_width'] = screenshot.get_width()
    save_data['screenshot_height'] = screenshot.get_height()
    save_data['time'] = datetime.datetime.now().strftime(TIME_FORMAT)
    save_data['version'] = SAVE_VERSION
    return save_data


def capture_screenshot(client):
    """
    :type client: tuxemon.core.client.Client
    """
    screenshot = pygame.Surface(client.screen.get_size())
    world = client.get_state_by_name("WorldState")
    world.draw(screenshot)
    return screenshot


def save(save_data, slot):
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
    save_path = prepare.SAVE_PATH + str(slot) + '.save'
    if prepare.SAVE_METHOD == "CBOR":
        text = cbor.dumps(save_data)
    else:
        text = json.dumps(save_data, indent=4, separators=(',', ': '))
    with open(save_path, 'w') as f:
        logger.info("Saving data to save file: " + save_path)
        # Don't dump straight to the file: if we crash it would corrupt the save_data
        f.write(text)


def load(slot):
    """Loads gamen state data from a shelved save file.

    :param slot: The save slot to load game data from.
    :type slot: Integer

    :rtype: Dictionary
    :returns: Dictionary containing game data to load.

    **Examples:**

    >>> core.load.load(1)

    """

    save_path = '{}{}.save'.format(prepare.SAVE_PATH, slot)
    save_data = open_save_file(save_path)
    if save_data:
        return upgrade_save(save_data)
    elif save_data is None:
        # File not found; it probably wasn't ever created, so don't panic
        return None
    else:
        save_data["error"] = "Save file corrupted"
        save_data["player_name"] = "BROKEN SAVE!"
        logger.error("Failed loading save file.")
        return save_data


def open_save_file(save_path):
    try:
        with open(save_path) as save_file:
            try:
                return json.load(save_file)
            except ValueError as e:
                logger.error("cannot decode JSON: %s", save_path)

            try:
                return cbor.load(save_file)
            except ValueError as e:
                logger.error("cannot decode save CBOR: %s", save_path)

            return {}

    except OSError as e:
        logger.info(e)
        return None


def get_index_of_latest_save():
    times = []
    for slot_index in range(3):
        save_path = '{}{}.save'.format(prepare.SAVE_PATH, slot_index + 1)
        save_data = open_save_file(save_path)
        if save_data is not None:
            time_of_save = datetime.datetime.strptime(save_data['time'], TIME_FORMAT)
            times.append((slot_index, time_of_save))
    if len(times) > 0:
        s = max(times, key=itemgetter(1))
        return s[0]
    else:
        return None
