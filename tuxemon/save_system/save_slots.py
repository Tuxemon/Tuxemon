# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


def ui_to_save_index(global_ui_index: int) -> int:
    """
    Convert a *global* UI index (0-based) to a save slot number (1-based).
    """
    return global_ui_index + 1


def save_index_to_ui(save_index: int) -> int:
    """
    Convert a save slot number (1-based) to a *global* UI index (0-based).
    """
    return save_index - 1


def resolve_save_index(index: int | None) -> int:
    """
    Convert event-action index to actual save slot number.
    index=None → invalid
    """
    if index is None:
        raise ValueError("resolve_save_index() called with index=None")

    return ui_to_save_index(index)
