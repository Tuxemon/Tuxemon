# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

TIME_FORMAT = "%Y-%m-%d %H:%M"


class WorldSave(BaseModel):
    factions_manager: dict[str, Any] = Field(default_factory=dict)
    menu_flags: dict[str, bool] = Field(default_factory=dict)


class SessionSave(BaseModel):
    uuid: str | None = Field(default=None)
    start_time: str | None = Field(default=None)
    duration: float | None = Field(default=None)
    total_playtime: float | None = Field(default=None)


class NPCState(BaseModel):
    instance_id: str | None = None
    is_player: bool = False
    position: list[float] | None = Field(
        default=None,
        description=(
            "Continuous world-space coordinates [x, y] in floating-point. "
            "This is the authoritative position used by physics and movement."
        ),
    )
    tile_pos: tuple[int, int] | None = Field(
        default=None,
        description=(
            "Discrete tile-space coordinates (x, y) in integers. "
            "Derived from world_position and used for grid-based logic. "
            "Kept for compatibility and debugging."
        ),
    )
    current_map: str | None = None
    facing: str | None = None
    gender: str | None = None
    birthdate: tuple[int, int] | None = None
    game_variables: dict[str, Any] = Field(default_factory=dict)
    battles: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    tuxepedia: Mapping[str, Any] = Field(default_factory=dict)
    relationships: Mapping[str, Any] = Field(default_factory=dict)
    money: Mapping[str, Any] = Field(default_factory=dict)
    appearance: dict[str, Any] = Field(default_factory=dict)
    missions: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    items: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    monsters: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    player_name: str | None = None
    player_slug: str | None = None
    player_steps: float | None = None
    monster_boxes: Mapping[str, list[Mapping[str, Any]]] = Field(
        default_factory=dict
    )
    item_boxes: Mapping[str, list[Mapping[str, Any]]] = Field(
        default_factory=dict
    )
    monster_box_metadata: Mapping[str, Any] = Field(default_factory=dict)
    item_box_metadata: Mapping[str, Any] = Field(default_factory=dict)
    daycare: dict[str, Any] = Field(default_factory=dict)
    teleport_faint: Mapping[str, Any] = Field(default_factory=dict)
    tracker: Mapping[str, Any] = Field(default_factory=dict)
    step_tracker: Mapping[str, Any] = Field(default_factory=dict)
    unlocked_letters: Mapping[str, Any] = Field(default_factory=dict)
    evolution_registry: Mapping[str, Any] = Field(default_factory=dict)
    routing_policy: str | None = None


class SaveData(BaseModel):
    screenshot: str | None = Field(default=None)
    screenshot_width: int | None = Field(default=None)
    screenshot_height: int | None = Field(default=None)
    time: str | None = Field(default=None)
    version: int | None = Field(default=None)
    npc_state: NPCState | None = Field(default=None)
    world_state: WorldSave | None = Field(default=None)
    session_state: SessionSave | None = Field(default=None)
    shop_stock: dict[str, dict[str, Any]] = Field(default_factory=dict)
    persistent_state: list[NPCState] = Field(default_factory=list)
