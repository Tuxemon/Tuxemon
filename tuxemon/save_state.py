# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel, Field

TIME_FORMAT = "%Y-%m-%d %H:%M"


class WorldSave(BaseModel):
    factions_manager: dict[str, Any] = Field(default_factory=dict)
    menu_flags: dict[str, bool] = Field(default_factory=dict)


class SessionSave(BaseModel):
    uuid: Optional[str] = Field(default=None)
    start_time: Optional[str] = Field(default=None)
    duration: Optional[float] = Field(default=None)
    total_playtime: Optional[float] = Field(default=None)


class NPCState(BaseModel):
    current_map: Optional[str] = Field(default=None)
    facing: Optional[str] = Field(default=None)
    game_variables: dict[str, Any] = Field(default_factory=dict)
    battles: list[Mapping[str, Any]] = Field(default_factory=list)
    tuxepedia: dict[str, Any] = Field(default_factory=dict)
    relationships: dict[str, Any] = Field(default_factory=dict)
    money: dict[str, Any] = Field(default_factory=dict)
    template: dict[str, Any] = Field(default_factory=dict)
    missions: list[Mapping[str, Any]] = Field(default_factory=list)
    items: list[Mapping[str, Any]] = Field(default_factory=list)
    monsters: list[Mapping[str, Any]] = Field(default_factory=list)
    player_name: Optional[str] = Field(default=None)
    player_slug: Optional[str] = Field(default=None)
    player_steps: Optional[float] = Field(default=None)
    monster_boxes: dict[str, list[Mapping[str, Any]]] = Field(
        default_factory=dict
    )
    item_boxes: dict[str, list[Mapping[str, Any]]] = Field(
        default_factory=dict
    )
    monster_box_metadata: dict[str, Any] = Field(default_factory=dict)
    item_box_metadata: dict[str, Any] = Field(default_factory=dict)
    tile_pos: Optional[tuple[int, int]] = Field(default=None)
    teleport_faint: dict[str, Any] = Field(default_factory=dict)
    tracker: dict[str, Any] = Field(default_factory=dict)
    step_tracker: dict[str, Any] = Field(default_factory=dict)
    unlocked_letters: dict[str, Any] = Field(default_factory=dict)
    evolution_registry: dict[str, Any] = Field(default_factory=dict)
    routing_policy: Optional[str] = Field(default=None)


class SaveData(BaseModel):
    screenshot: Optional[str] = Field(default=None)
    screenshot_width: Optional[int] = Field(default=None)
    screenshot_height: Optional[int] = Field(default=None)
    time: Optional[str] = Field(default=None)
    version: Optional[int] = Field(default=None)
    npc_state: Optional[NPCState] = Field(default=None)
    world_state: Optional[WorldSave] = Field(default=None)
    session_state: Optional[SessionSave] = Field(default=None)
    shop_stock: dict[str, dict[str, Any]] = Field(default_factory=dict)
    persistent_state: list[NPCState] = Field(default_factory=list)
