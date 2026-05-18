# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class EntryNotFoundError(Exception):
    """Raised when a specific data entry slug is not found in the database."""


class DatabaseConfig(BaseModel):
    """Configuration settings for the mod database system."""

    model_config = ConfigDict(extra="forbid")
    model_map: dict[str, str] = Field(
        ...,
        description="Maps model names to Python class paths for game data types.",
    )
    mod_base_path: str = Field(
        ..., description="Base directory where all game mods are located."
    )
    mod_db_subfolder: str = Field(
        ..., description="Subfolder within each mod for its database files."
    )
    file_extensions: list[str] = Field(
        default_factory=list,
        description="Recognized file extensions for data entries (e.g., ['.json', '.yaml']).",
    )
    default_lookup_table: str = Field(
        ...,
        description="Fallback table used when no specific table is provided.",
    )
    active_mods: list[str] = Field(
        default_factory=list, description="List of enabled mod directories."
    )
    mod_activation: dict[str, bool] = Field(
        default_factory=dict, description="Activation status for each mod."
    )
    mod_tables: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Tables each mod contributes data to.",
    )
    mod_table_exclusions: dict[str, list[str]] = Field(
        default_factory=dict, description="Tables excluded by specific mods."
    )
    mod_dependencies: dict[str, list[str]] = Field(
        default_factory=dict, description="Mod load-order dependencies."
    )


class ModMetadata(BaseModel):
    """Metadata structure for a single mod (from mod.yaml)."""

    model_config = ConfigDict(extra="forbid")
    slug: str = Field(
        ..., description="The unique, short identifier for the mod."
    )
    description: str = Field(
        ..., description="A brief summary of the mod's purpose."
    )
    name: str = Field(..., description="Human-readable name of the mod.")
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version (e.g., 1.2.3).",
    )
    starting_map: str = Field(
        ..., description="Initial map file (.tmx) where the player begins."
    )
    sprite: str = Field(
        ..., description="Base filename of the player's overworld sprite."
    )
    combat_sheet: str = Field(
        ...,
        description="Base filename of the player's front-facing combat sprite.",
    )
    authors: list[str] = Field(
        default_factory=list, description="List of authors or contributors."
    )
    startup_rules: list[str] = Field(
        default_factory=list, description="List of rules (startup)."
    )
    starting_players: list[str] = Field(
        default_factory=list,
        description="Initial slugs available to the player.",
    )
    starting_names: list[str] = Field(
        default_factory=list,
        description="Possible player names to choose from.",
    )
    starting_position: tuple[int, int] = Field(
        default=(0, 0),
        description="Initial player position as (x, y) coordinates.",
    )
    starting_money: tuple[int, int] = Field(
        default=(500, 500), description="Starting money range as (min, max)."
    )
