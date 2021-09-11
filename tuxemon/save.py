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
# save Handle save games.
#
#

from __future__ import annotations
import base64
import datetime
import json
import logging
from operator import itemgetter

import pygame

from tuxemon import prepare
from tuxemon.save_upgrader import SAVE_VERSION, upgrade_save
from tuxemon.session import Session
from typing import Mapping, Any, Optional, Dict
from tuxemon.client import LocalPygameClient
from tuxemon.states.world.worldstate import WorldState
from tuxemon import prepare
from tuxemon.lib import compress_json

try:
    import cbor
except ImportError:
    prepare.SAVE_METHOD = "JSON"

logger = logging.getLogger(__name__)

slot_number = None
TIME_FORMAT = "%Y-%m-%d %H:%M"
config = prepare.CONFIG


def capture_screenshot(client: LocalPygameClient) -> pygame.surface.Surface:
    """
    Capture a screenshot.

    Parameters:
            client: Tuxemon client.

    Returns:
            Captured image.

    """
    screenshot = pygame.Surface(client.screen.get_size())
    world = client.get_state_by_name(WorldState)
    assert world
    world.draw(screenshot)
    return screenshot


def get_save_data(session: Session) -> Mapping[str, Any]:
    """
    Gets a dictionary which represents the state of the session.

    Parameters:
            session: Game session.

    Returns:
            Game data to save, must be JSON encodable.

    """
    save_data = session.player.get_state(session)
    screenshot = capture_screenshot(session.client)
    save_data["screenshot"] = base64.b64encode(
        pygame.image.tostring(screenshot, "RGB")).decode("utf-8")
    save_data["screenshot_width"] = screenshot.get_width()
    save_data["screenshot_height"] = screenshot.get_height()
    save_data["time"] = datetime.datetime.now().strftime(TIME_FORMAT)
    save_data["version"] = SAVE_VERSION
    return save_data


def open_save_file(save_path: str) -> Optional[Dict[str, Any]]:

    if config.compress_save:
        try:
            DATA = compress_json.load(
                save_path
            )
            return DATA
        except Exception as e:
            logger.info(e)
            return None
    else:
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


def save(
        save_data: Mapping[str, Any],
        slot: int,
) -> None:
    """
    Saves the current game state to a file using gzip compressed JSON.

    Parameters:
            save_data: The data to save.
            slot: The save slot to save the data to.

    """
    # Save a screenshot of the current frame
    # if/else paradise
    if config.compress_save:
        if config.csave_lzma:
            save_path = prepare.SAVE_PATH + str(slot) + ".csave.lza"
            text = compress_json.dump(
                save_data,
                save_path,
                compression_kwargs={},
                json_kwargs={"indent": 4, 'separators': (",", ": ")}
            )
        else:
            save_path = prepare.SAVE_PATH + str(slot) + ".csave.gz"
            text = compress_json.dump(
                save_data,
                save_path,
                compression_kwargs={'compresslevel': 9},
                json_kwargs={"indent": 4, 'separators': (",", ": ")}
            )
    else:
        save_path = prepare.SAVE_PATH + str(slot) + ".save"
        if prepare.SAVE_METHOD == "CBOR":
            text = cbor.dumps(save_data)
        else:
            text = json.dumps(save_data, indent=4, separators=(",", ": "))
        with open(save_path, "w") as f:
            logger.info("Saving data to save file: " + save_path)
            # Don't dump straight to the file: if we crash it would corrupt
            # the save_data
            f.write(text)
    #text = json.dumps(save_data, indent=4, separators=(",", ": "))


def load(slot: int) -> Optional[Mapping[str, Any]]:
    """
    Loads game state data from a save file.

    Parameters:
            slot: The save slot to load game data from.

    Returns:
            Dictionary containing game data to load.

    """
    if config.compress_save:
        if config.csave_lzma:
            save_path = f"{prepare.SAVE_PATH}{slot}.csave.lza"
        else:
            save_path = f"{prepare.SAVE_PATH}{slot}.csave.gz"
    else:
        save_path = f"{prepare.SAVE_PATH}{slot}.save"

    save_data = open_save_file(save_path)

    # DEBUG STUFF HERE
    #print("ayo look here")
    # print(save_data)

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


def get_index_of_latest_save() -> Optional[int]:
    times = []
    for slot_index in range(3):
        if config.compress_save:
            if config.csave_lzma:
                save_path = f"{prepare.SAVE_PATH}{slot_index + 1}.csave.lza"
            else:
                save_path = f"{prepare.SAVE_PATH}{slot_index + 1}.csave.gz"
        else:
            save_path = f"{prepare.SAVE_PATH}{slot_index + 1}.save"
        save_data = open_save_file(save_path)
        if save_data is not None:
            time_of_save = datetime.datetime.strptime(save_data["time"], TIME_FORMAT)
            times.append((slot_index, time_of_save))
    if len(times) > 0:
        s = max(times, key=itemgetter(1))
        return s[0]
    else:
        return None
