# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

AUTOSAVE_SLOT: int = 0


def ui_to_save_index(global_ui_index: int) -> int:
    """
    Convert a UI slot index (0-2) into a save slot number (1-3); autosave uses slot 0.
    """
    return global_ui_index + 1


def save_index_to_ui(save_index: int) -> int:
    """
    Convert a save slot number (1-3) into a UI slot index (0-2); autosave (0) has no UI slot.
    """
    return save_index - 1


def resolve_save_index(index: int | None) -> int:
    """
    Convert an event-action UI index (0-2) into a save slot number (1-3); autosave is slot 0.
    """
    if index is None:
        raise ValueError("resolve_save_index() called with index=None")

    return ui_to_save_index(index)
