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
from enum import Enum
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from pygame.image import tobytes
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.save_state import TIME_FORMAT, SaveData
from tuxemon.save_upgrader import SAVE_VERSION, upgrade_save

if TYPE_CHECKING:
    from tuxemon.session import Session

try:
    import cbor
except ImportError:
    prepare.SAVE_METHOD = "JSON"


T = TypeVar("T")


logger = logging.getLogger(__name__)

slot_number: Optional[int] = None
config = prepare.CONFIG


class SaveMethod(Enum):
    JSON = "JSON"
    CBOR = "CBOR"

    @classmethod
    def from_string(cls, method_str: str) -> SaveMethod:
        try:
            return cls[method_str.upper()]
        except KeyError:
            # Fallback to JSON if an unknown method is encountered or cbor not available
            return cls.JSON


def capture_screenshot(session: Session) -> Surface:
    """Capture a screenshot."""
    screenshot = Surface(prepare.SCREEN_SIZE)
    session.world.draw(screenshot)
    return screenshot


def get_save_data(session: Session) -> SaveData:
    """
    Gets a dictionary which represents the state of the session.

    Parameters:
        session: Game session.

    Returns:
        Game data to save, must be JSON encodable.
    """
    screenshot = capture_screenshot(session)
    npc_state = session.player.get_state(session)
    world_state = session.world.get_state(session)
    session_state = session.get_state()

    return {
        "screenshot": b64encode(tobytes(screenshot, "RGB")).decode(),
        "screenshot_width": screenshot.get_width(),
        "screenshot_height": screenshot.get_height(),
        "time": datetime.now().strftime(TIME_FORMAT),
        "version": SAVE_VERSION,
        "npc_state": npc_state,
        "world_state": world_state,
        "session_state": session_state,
    }


def _get_save_extension() -> str:
    save_format = config.compress_save
    return "save" if save_format is None else f"csave.{save_format}"


def get_save_path(slot: int) -> Path:
    extension = _get_save_extension()
    return prepare.SAVE_PATH.parent / f"slot{slot}.{extension}"


def save_action(
    path: Path,
    mode: str,
    action_function: Callable[[Any, Any], T],
    save_method: SaveMethod,
    compress_save: Optional[str] = None,
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    serializer_kwargs: Optional[Mapping[str, Any]] = None,
) -> T:
    if compression_kwargs is None:
        compression_kwargs = {}

    if serializer_kwargs is None:
        serializer_kwargs = {}

    open_function = open
    if compress_save is not None:
        compression_tool = importlib.import_module(compress_save)
        open_function = compression_tool.open

    is_binary_mode = save_method == SaveMethod.CBOR

    actual_mode = mode
    if is_binary_mode and "t" in mode:
        actual_mode = mode.replace("t", "b")
    elif not is_binary_mode and "b" in mode:
        actual_mode = mode.replace("b", "t")

    with open_function(
        path,
        mode=actual_mode,
        encoding="utf-8" if not is_binary_mode else None,
        **compression_kwargs,
    ) as file:
        return action_function(file, serializer_kwargs)


def dump_data(
    obj: Any,
    path: Path,
    save_method: SaveMethod,
    compress_save: Optional[str] = None,
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    serializer_kwargs: Optional[Mapping[str, Any]] = None,
) -> None:
    def action_function(
        file: Any,
        serializer_kwargs: Mapping[str, Any],
    ) -> None:
        if save_method == SaveMethod.JSON:
            json.dump(obj, file, **serializer_kwargs)
        elif save_method == SaveMethod.CBOR:
            cbor.dump(obj, file, **serializer_kwargs)
        else:
            raise ValueError(f"Unsupported save method: {save_method}")

    mode = "wt" if save_method == SaveMethod.JSON else "wb"

    return save_action(
        path=path,
        mode=mode,
        action_function=action_function,
        save_method=save_method,
        compress_save=compress_save,
        compression_kwargs=compression_kwargs,
        serializer_kwargs=serializer_kwargs,
    )


def load_data(
    path: Path,
    save_method: SaveMethod,
    compress_save: Optional[str] = None,
    compression_kwargs: Optional[Mapping[str, Any]] = None,
    serializer_kwargs: Optional[Mapping[str, Any]] = None,
) -> Any:
    if compression_kwargs is None:
        compression_kwargs = {}

    if serializer_kwargs is None:
        serializer_kwargs = {}

    open_function = open
    if compress_save is not None:
        compression_tool = importlib.import_module(compress_save)
        open_function = compression_tool.open

    mode = "rt" if save_method == SaveMethod.JSON else "rb"

    with open_function(
        path,
        mode=mode,
        encoding="utf-8" if save_method == SaveMethod.JSON else None,
        **compression_kwargs,
    ) as file:
        if save_method == SaveMethod.JSON:
            return json.load(file, **serializer_kwargs)
        elif save_method == SaveMethod.CBOR:
            return cbor.load(file, **serializer_kwargs)
        else:
            raise ValueError(f"Unsupported save method: {save_method}")


def open_save_file(save_path: Path) -> Optional[dict[str, Any]]:
    current_save_method = SaveMethod.from_string(prepare.SAVE_METHOD)

    package: dict[str, Any] = {}

    try:
        try:
            package = load_data(
                save_path,
                save_method=current_save_method,
                compress_save=config.compress_save,
            )
            return package
        except ValueError as e:
            logger.error(f"Cannot decode save: {save_path}", exc_info=True)
            return None
    except OSError as e:
        logger.info(f"OS Error when opening save file {save_path}: {e}")
        return None


def save(save_data: SaveData, slot: int) -> None:
    """
    Saves the current game state to a file using gzip compressed JSON.

    Parameters:
        save_data: The data to save.
        slot: The save slot to save the data to.
    """
    save_path = get_save_path(slot)
    save_path_tmp = save_path.with_suffix(save_path.suffix + ".tmp")
    json_kwargs = {
        "indent": 4,
        "separators": (",", ": "),
    }

    current_save_method = SaveMethod.from_string(prepare.SAVE_METHOD)
    logger.info(f"Saving data to save file: {save_path}")

    dump_data(
        save_data,
        save_path_tmp,
        save_method=current_save_method,
        compress_save=config.compress_save,
        serializer_kwargs=(
            json_kwargs if current_save_method == SaveMethod.JSON else {}
        ),
    )

    # Don't dump straight to the file: if we crash it would corrupt
    # the save_data
    # We use a temporal file plus atomic replacement instead
    os.replace(save_path_tmp.as_posix(), save_path.as_posix())


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
