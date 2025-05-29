# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import json
import logging
import os
from base64 import b64encode
from collections.abc import Callable, Mapping
from datetime import datetime
from operator import itemgetter
from typing import Any, Literal, Optional, TextIO, TypedDict, TypeVar

from pygame.image import tobytes
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.npc import NPCState
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


class SaveData(TypedDict, total=False):
    screenshot: str
    screenshot_width: int
    screenshot_height: int
    time: str
    version: int
    npc_state: NPCState


def capture_screenshot(client: LocalPygameClient) -> Surface:
    """
    Capture a screenshot.

    Parameters:
        client: Tuxemon client.

    Returns:
        Captured image.
    """
    screenshot = Surface(client.screen.get_size())
    world = client.get_state_by_name(WorldState)
    world.draw(screenshot)
    return screenshot


def get_save_data(session: Session) -> SaveData:
    """
    Gets a dictionary which represents the state of the session.

    Parameters:
        session: Game session.

    Returns:
        Game data to save, must be JSON encodable.
    """
    screenshot = capture_screenshot(session.client)
    npc_state = session.player.get_state(session)

    return {
        "screenshot": b64encode(tobytes(screenshot, "RGB")).decode(),
        "screenshot_width": screenshot.get_width(),
        "screenshot_height": screenshot.get_height(),
        "time": datetime.now().strftime(TIME_FORMAT),
        "version": SAVE_VERSION,
        "npc_state": npc_state,
    }


def _get_save_extension() -> str:
    save_format = config.compress_save

    return "save" if save_format is None else f"csave.{save_format}"


def get_save_path(slot: int) -> str:
    extension = _get_save_extension()
    return f"{prepare.SAVE_PATH.as_posix()}{slot}.{extension}"


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


def open_save_file(save_path: str) -> Optional[dict[str, Any]]:
    package: dict[str, Any] = {}
    try:
        try:
            if config.compress_save is None and prepare.SAVE_METHOD == "CBOR":
                package = cbor.load(save_path)
                return package
            else:
                package = json_load(save_path)
                return package
        except ValueError as e:
            logger.error(f"Cannot decode save: {save_path}")
            return None
    except OSError as e:
        logger.info(e)
        return None


def save(save_data: SaveData, slot: int) -> None:
    """
    Saves the current game state to a file using gzip compressed JSON.

    Parameters:
        save_data: The data to save.
        slot: The save slot to save the data to.
    """
    save_path = get_save_path(slot)
    save_path_tmp = save_path + ".tmp"
    json_kwargs = {
        "indent": 4,
        "separators": (",", ": "),
    }

    logger.info(f"Saving data to save file: {save_path}")
    if config.compress_save is None and prepare.SAVE_METHOD == "CBOR":
        cbor.dump(save_data, save_path_tmp)
    else:
        json_dump(save_data, save_path_tmp, json_kwargs=json_kwargs)

    # Don't dump straight to the file: if we crash it would corrupt
    # the save_data
    # We use a temporal file plus atomic replacement instead
    os.replace(save_path_tmp, save_path)


def load(slot: int) -> Optional[SaveData]:
    """
    Loads game state data from a save file.

    Parameters:
        slot: The save slot to load game data from.

    Returns:
        Dictionary containing game data to load.
    """
    save_path = get_save_path(slot)
    save_data = open_save_file(save_path)

    if save_data is None:
        # File not found; it probably wasn't ever created, so don't panic
        return None
    return upgrade_save(save_data)


def get_index_of_latest_save() -> Optional[int]:
    times = []
    for slot_index in range(3):
        save_path = get_save_path(slot_index + 1)
        save_data = open_save_file(save_path)
        if save_data is not None:
            time_of_save = datetime.strptime(
                save_data["time"],
                TIME_FORMAT,
            )
            times.append((slot_index, time_of_save))
    if len(times) > 0:
        s = max(times, key=itemgetter(1))
        return s[0]
    else:
        return None
