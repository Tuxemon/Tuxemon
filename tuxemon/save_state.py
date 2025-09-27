# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict


class SaveData(TypedDict, total=False):
    screenshot: str
    screenshot_width: int
    screenshot_height: int
    time: str
    version: int
    npc_state: NPCState
    world_state: WorldSave


class WorldSave(TypedDict, total=False):
    factions_manager: dict[str, Any]
    menu_flags: dict[str, bool]


class NPCState(TypedDict, total=False):
    current_map: str
    facing: str
    game_variables: dict[str, Any]
    battles: Sequence[Mapping[str, Any]]
    tuxepedia: Mapping[str, Any]
    relationships: Mapping[str, Any]
    money: Mapping[str, Any]
    template: dict[str, Any]
    missions: Sequence[Mapping[str, Any]]
    items: Sequence[Mapping[str, Any]]
    monsters: Sequence[Mapping[str, Any]]
    player_name: str
    player_slug: str
    player_steps: float
    monster_boxes: dict[str, Sequence[Mapping[str, Any]]]
    item_boxes: dict[str, Sequence[Mapping[str, Any]]]
    tile_pos: tuple[int, int]
    teleport_faint: tuple[str, int, int]
    tracker: Mapping[str, Any]
    step_tracker: Mapping[str, Any]
    unlocked_letters: Mapping[str, Any]
    evolution_registry: Mapping[str, Any]
