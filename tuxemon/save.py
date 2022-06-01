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
import importlib
import json
import logging
import os
from operator import itemgetter
from typing import Any, Callable, Literal, Mapping, Optional, TextIO, TypeVar

import pygame

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.save_upgrader import SAVE_VERSION, upgrade_save
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

try:
    import cbor
except ImportError:
    prepare.SAVE_METHOD = "JSON"


T = TypeVar("T")


logger = logging.getLogger(__name__)

slot_number: Optional[int] = None
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


def _get_save_extension() -> str:
    save_format = config.compress_save

    return "save" if save_format is None else f"csave.{save_format}"


def get_save_path(slot: int) -> str:
    extension = _get_save_extension()
    return f"{prepare.SAVE_PATH}{slot}.{extension}"


def json_action(
    path: str,
    mode: Literal["wt", "rt"],
    action_function: Callable[[TextIO, Mapping[str, Any]], T],
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    json_kwargs: Optional[Mapping[str, Any]] = None,
) -> T:
    if compression_kwargs is None:
        compression_kwargs = {}

    if json_kwargs is None:
        json_kwargs = {}

    if config.compress_save is None:
        open_function = open
    else:
        compression_tool = importlib.import_module(config.compress_save)
        open_function = compression_tool.open

    with open_function(
        path,
        mode=mode,
        encoding="utf-8",
        **compression_kwargs,
    ) as file:
        return action_function(file, json_kwargs)


def json_dump(
    obj: Any,
    path: str,
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    json_kwargs: Optional[Mapping[str, Any]] = None,
) -> None:

    def action_function(
        file: TextIO,
        json_kwargs: Mapping[str, Any],
    ) -> None:
        json.dump(obj, file, **json_kwargs)

    return json_action(
        path=path,
        mode="wt",
        action_function=action_function,
        compression_kwargs=compression_kwargs,
        json_kwargs=json_kwargs,
    )


def json_load(
    path: str,
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    json_kwargs: Optional[Mapping[str, Any]] = None,
) -> Any:

    def action_function(
        file: TextIO,
        json_kwargs: Mapping[str, Any],
    ) -> Any:
        return json.load(file, **json_kwargs)

    return json_action(
        path=path,
        mode="rt",
        action_function=action_function,
        compression_kwargs=compression_kwargs,
        json_kwargs=json_kwargs,
    )


def open_save_file(save_path: str) -> Any:

    try:
        try:
            if config.compress_save is None and prepare.SAVE_METHOD == "CBOR":
                return cbor.load(save_path)
            else:
                return json_load(save_path)
        except ValueError as e:
            logger.error("Cannot decode save: %s", save_path)
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

    save_path = get_save_path(slot)
    save_path_tmp = save_path + ".tmp"
    json_kwargs = {
        "indent": 4,
        "separators": (",", ": "),
    }

    logger.info("Saving data to save file: %s", save_path)
    if config.compress_save is None and prepare.SAVE_METHOD == "CBOR":
        cbor.dump(save_data, save_path_tmp)
    else:
        json_dump(save_data, save_path_tmp, json_kwargs=json_kwargs)

    # Don't dump straight to the file: if we crash it would corrupt
    # the save_data
    # We use a temporal file plus atomic replacement instead
    os.replace(save_path_tmp, save_path)


def load(slot: int) -> Optional[Mapping[str, Any]]:
    """
    Loads game state data from a save file.

    Parameters:
        slot: The save slot to load game data from.

    Returns:
        Dictionary containing game data to load.

    """
    save_path = get_save_path(slot)
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


def get_index_of_latest_save() -> Optional[int]:
    times = []
    for slot_index in range(3):
        save_path = get_save_path(slot_index + 1)
        save_data = open_save_file(save_path)
        if save_data is not None:
            time_of_save = datetime.datetime.strptime(save_data["time"], TIME_FORMAT)
            times.append((slot_index, time_of_save))
    if len(times) > 0:
        s = max(times, key=itemgetter(1))
        return s[0]
    else:
        return None
