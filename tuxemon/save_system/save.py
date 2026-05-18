# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
from typing import TYPE_CHECKING, Any, TypeVar

from pygame.image import tobytes
from pygame.surface import Surface

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import dump_yaml_io, load_yaml
from tuxemon.save_system.save_state import TIME_FORMAT, SaveData
from tuxemon.save_system.save_upgrader import SAVE_VERSION, upgrade_save
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.session import Session

try:
    import cbor
except ImportError:
    CONFIG.update_attribute("game", "save_method", "json", save=False)


T = TypeVar("T")

logger = logging.getLogger(__name__)


class SaveMethod(Enum):
    JSON = "json"
    CBOR = "cbor"
    YAML = "yaml"

    @classmethod
    def from_string(cls, method_str: str) -> SaveMethod:
        try:
            return cls[method_str.upper()]
        except KeyError:
            # Fallback to JSON if an unknown method is encountered or cbor not available
            return cls.JSON


def capture_screenshot(session: Session) -> Surface:
    """Capture a screenshot."""
    screenshot = Surface(session.client.context.resolution)
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
    persistent_npcs = session.client.npc_manager.get_persistent_npc_states(
        session
    )

    return SaveData(
        screenshot=b64encode(tobytes(screenshot, "RGB")).decode(),
        screenshot_width=screenshot.get_width(),
        screenshot_height=screenshot.get_height(),
        time=datetime.now().strftime(TIME_FORMAT),
        version=SAVE_VERSION,
        npc_state=npc_state,
        world_state=world_state,
        session_state=session_state,
        shop_stock=session.client.shop_manager.dump_to_dict(),
        persistent_state=persistent_npcs,
    )


def save_action(
    path: Path,
    mode: str,
    action_function: Callable[[Any, Any], T],
    compress_save: str | None = None,
    compression_kwargs: Mapping[str, Any] | None = None,
    serializer_kwargs: Mapping[str, Any] | None = None,
) -> T:
    """
    Opens a file (optionally compressed) and calls action_function with it.
    """
    if compression_kwargs is None:
        compression_kwargs = {}

    if serializer_kwargs is None:
        serializer_kwargs = {}

    open_function = open
    if compress_save is not None:
        compression_tool = importlib.import_module(compress_save)
        open_function = compression_tool.open

    is_binary_mode = "b" in mode

    with open_function(
        path,
        mode=mode,
        encoding=None if is_binary_mode else "utf-8",
        **compression_kwargs,
    ) as file:
        return action_function(file, serializer_kwargs)


def dump_data(
    obj: SaveData,
    path: Path,
    save_method: SaveMethod,
    compress_save: str | None = None,
    compression_kwargs: Mapping[str, Any] | None = None,
    serializer_kwargs: Mapping[str, Any] | None = None,
) -> None:
    def action_function(
        file: Any,
        serializer_kwargs: Mapping[str, Any],
    ) -> None:
        serializable_obj = obj.model_dump()

        if save_method == SaveMethod.JSON:
            json.dump(serializable_obj, file, **serializer_kwargs)

        elif save_method == SaveMethod.CBOR:
            cbor.dump(serializable_obj, file, **serializer_kwargs)

        elif save_method == SaveMethod.YAML:
            dump_yaml_io(
                file,
                serializable_obj,
                default_flow_style=False,
                **serializer_kwargs,
            )

        else:
            raise ValueError(f"Unsupported save method: {save_method}")

    mode = "wb" if save_method == SaveMethod.CBOR else "wt"

    save_action(
        path=path,
        mode=mode,
        action_function=action_function,
        compress_save=compress_save,
        compression_kwargs=compression_kwargs,
        serializer_kwargs=serializer_kwargs,
    )


def load_data(
    path: Path,
    save_method: SaveMethod,
    compress_save: str | None = None,
    compression_kwargs: Mapping[str, Any] | None = None,
    serializer_kwargs: Mapping[str, Any] | None = None,
) -> Any:
    if compression_kwargs is None:
        compression_kwargs = {}

    if serializer_kwargs is None:
        serializer_kwargs = {}

    open_function = open
    if compress_save is not None:
        compression_tool = importlib.import_module(compress_save)
        open_function = compression_tool.open

    mode = "rb" if save_method == SaveMethod.CBOR else "rt"

    with open_function(
        path,
        mode=mode,
        encoding=(None if save_method == SaveMethod.CBOR else "utf-8"),
        **compression_kwargs,
    ) as file:
        if save_method == SaveMethod.JSON:
            return json.load(file, **serializer_kwargs)
        elif save_method == SaveMethod.CBOR:
            return cbor.load(file, **serializer_kwargs)
        elif save_method == SaveMethod.YAML:
            # load_yaml expects a Path, not a file handle.
            # Compressed YAML is not supported; if compress_save is set
            # alongside YAML the open() above will have already raised.
            return load_yaml(path)
        else:
            raise ValueError(f"Unsupported save method: {save_method}")


def open_save_file(save_path: Path) -> dict[str, Any] | None:
    """
    Opens and decodes the save file from disk.

    Parameters:
        save_path: Path to the save file.

    Returns:
        Raw dictionary of save data, or None if the file is missing or corrupted.
    """
    current_save_method = SaveMethod.from_string(CONFIG.save_method)

    try:
        data = load_data(
            save_path,
            save_method=current_save_method,
            compress_save=CONFIG.compress_save,
        )
        # load_data returns Any; narrow to dict[str, Any] before returning.
        if not isinstance(data, dict):
            logger.error(
                f"Save file has unexpected structure (got {type(data).__name__}): {save_path}"
            )
            return None
        return data
    except ValueError:
        logger.error(f"Cannot decode save: {save_path}", exc_info=True)
        return None
    except OSError as e:
        logger.info(f"OS error when opening save file {save_path}: {e}")
        return None


def get_save_path(
    slot: int, prefix: str | None = None, extension: str | None = None
) -> Path:
    extension = CONFIG.save_extension if extension is None else extension
    prefix = CONFIG.save_prefix if prefix is None else prefix
    final_extension = (
        extension
        if CONFIG.compress_save is None
        else f"c{extension}.{CONFIG.compress_save}"
    )
    return paths.USER_GAME_SAVE_DIR / f"{prefix}{slot}.{final_extension}"


def save(save_data: SaveData, save_path: Path) -> None:
    """
    Saves the current game state to disk using the format and compression
    specified in CONFIG (save_method and compress_save).

    Uses a temporary file and atomic replacement to avoid corrupting the
    existing save if a crash occurs mid-write.

    Parameters:
        save_data: The data to save.
        save_path: The full path where the save file should be written.
    """
    save_path_tmp = save_path.with_suffix(save_path.suffix + ".tmp")
    current_save_method = SaveMethod.from_string(CONFIG.save_method)

    logger.info(f"Saving data to save file: {save_path}")

    dump_data(
        save_data,
        save_path_tmp,
        save_method=current_save_method,
        compress_save=CONFIG.compress_save,
        serializer_kwargs=(
            {"indent": 4, "separators": (",", ": ")}
            if current_save_method == SaveMethod.JSON
            else {}
        ),
    )

    # Write to a temp file first; if we crash mid-write the original is intact.
    os.replace(save_path_tmp.as_posix(), save_path.as_posix())


def load(save_path: Path) -> SaveData | None:
    """
    Loads game state data from a save file.

    Parameters:
        save_path: The full path to the save file to load.

    Returns:
        A SaveData object containing the loaded game state, or None if
        the file doesn't exist or is unreadable.
    """
    raw_data = open_save_file(save_path)

    if raw_data is None:
        # File not found or corrupt; don't panic, just return None.
        return None

    upgraded_data = upgrade_save(raw_data)
    return SaveData(**upgraded_data)


def get_index_of_latest_save() -> int | None:
    """
    Returns the slot index (0-based) of the most recently saved game,
    or None if no saves exist.
    """
    times = []
    for slot_index in range(CONFIG.save_slots):
        save_path = get_save_path(slot_index + 1)
        save_data = open_save_file(save_path)
        if save_data is not None:
            time_of_save = datetime.strptime(
                save_data["time"],
                TIME_FORMAT,
            )
            times.append((slot_index, time_of_save))

    if times:
        return max(times, key=itemgetter(1))[0]

    return None
