# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tuxemon.constants.paths import mods_folder
from tuxemon.database.yaml_utils import load_yaml

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus

logger = logging.getLogger(__name__)


class RelationshipStatus(Enum):
    HATED = 0
    INDIFFERENT = 1
    ACQUAINTANCE = 2
    FRIEND = 3
    BEST_FRIEND = 4


class RelationshipConstants:
    STRENGTH: tuple[int, int] = (0, 100)
    TIERS: dict[int, RelationshipStatus] = {}
    PROFILES: dict[str, dict[str, float | int]] = {}


@dataclass
class RelationshipConfig:
    strength_range: dict[str, int]
    tiers: dict[int, str]
    profiles: dict[str, dict[str, float | int]]


def load_relationship_config(file_path: Path) -> RelationshipConfig:
    data = load_yaml(file_path)
    return RelationshipConfig(**data)


def initialize_constants(config: RelationshipConfig) -> None:
    """Initializes RelationshipConstants from the loaded configuration."""
    RelationshipConstants.STRENGTH = (
        config.strength_range["min"],
        config.strength_range["max"],
    )
    RelationshipConstants.TIERS = {
        int(k): RelationshipStatus[v] for k, v in sorted(config.tiers.items())
    }
    RelationshipConstants.PROFILES = config.profiles


try:
    CONFIG_DATA = load_relationship_config(mods_folder / "relationships.yaml")
    initialize_constants(CONFIG_DATA)
except FileNotFoundError:
    logger.error(
        "relationships.yaml not found. Relationship constants not loaded."
    )
except Exception as e:
    logger.error(f"Error initializing relationship constants: {e}")


@dataclass
class Connection:
    relationship_type: str
    strength: int = 50
    steps: float = 0.0
    decay_rate: float = 0.01
    decay_threshold: int = 500

    def get_profile_value(self, key: str) -> float | int:
        profile = RelationshipConstants.PROFILES.get(
            self.relationship_type, RelationshipConstants.PROFILES["default"]
        )
        return profile.get(key, RelationshipConstants.PROFILES["default"][key])

    def get_status(self) -> RelationshipStatus:
        current_status = RelationshipStatus.HATED
        for min_strength, status in RelationshipConstants.TIERS.items():
            if self.strength >= min_strength:
                current_status = status
            else:
                break
        return current_status

    def apply_decay(self, current_steps: float) -> None:
        steps_since_last = current_steps - self.steps
        if steps_since_last >= self.decay_threshold:
            decay_multiplier = steps_since_last // self.decay_threshold
            decay_rate_mod = self.get_profile_value("decay_rate_mod")
            effective_decay_rate = self.decay_rate * decay_rate_mod
            decay_amount = decay_multiplier * effective_decay_rate

            new_strength = self.strength - round(decay_amount)
            self.strength = max(
                RelationshipConstants.STRENGTH[0],
                min(new_strength, RelationshipConstants.STRENGTH[1]),
            )
            self.steps = current_steps - (
                steps_since_last % self.decay_threshold
            )

    def update_steps(self, current_steps: float) -> None:
        self.steps = current_steps

    def get_state(self) -> dict[str, Any]:
        """Returns a dictionary representing the state of the connection for saving."""
        return {
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "steps": self.steps,
            "decay_rate": self.decay_rate,
            "decay_threshold": self.decay_threshold,
        }


class Relationships:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self.connections: dict[str, Connection] = {}
        self._event_bus.subscribe(
            "relationship_modified", self._apply_modification
        )

    def _apply_modification(
        self, npc_slug: str, attribute: str, value: float, **kwargs: Any
    ) -> None:
        if npc_slug not in self.connections:
            return

        if attribute == "decay_rate":
            self.update_connection_decay_rate(npc_slug, value)
        elif attribute == "decay_threshold":
            self.update_connection_decay_threshold(npc_slug, int(value))
        elif attribute == "strength":
            self.update_connection_strength(npc_slug, int(value))
        else:
            logger.error(
                f"{attribute} must be 'strength', 'decay_rate' or 'decay_threshold'"
            )

    def add_connection(
        self,
        slug: str,
        connection: Connection,
    ) -> None:
        """Adds a new connection."""
        self.connections[slug] = connection
        self._event_bus.publish(
            "relationship_added",
            slug=slug,
            connection=connection,
        )

    def remove_connection(self, slug: str) -> None:
        """Removes a connection by slug."""
        if slug in self.connections:
            del self.connections[slug]
            self._event_bus.publish(
                "relationship_removed",
                slug=slug,
            )

    def modify_connection_strength(self, slug: str, raw_change: int) -> None:
        """
        Adjusts the strength of an existing connection, applying separate
        profile modifiers for positive (gain) and negative (loss) changes.
        """
        connection = self.get_connection(slug)
        if connection:
            effective_change: int

            if raw_change > 0:
                gain_mod = connection.get_profile_value(
                    "strength_increase_mod"
                )
                effective_change = round(raw_change * gain_mod)
                event_name = "relationship_gained"

            elif raw_change < 0:
                # Note: raw_change is negative, mod should be positive.
                loss_mod = connection.get_profile_value(
                    "strength_decrease_mod"
                )
                effective_change = -round(abs(raw_change) * loss_mod)
                event_name = "relationship_lost"

            else:
                # raw_change is 0, no change needed
                return

            new_strength = connection.strength + effective_change
            self.update_connection_strength(slug, new_strength)

            self._event_bus.publish(
                event_name,
                slug=slug,
                raw_change=raw_change,
                effective_change=effective_change,
                strength=new_strength,
            )

    def update_connection_strength(self, slug: str, new_strength: int) -> None:
        """Updates strength, clamped to RelationshipConstants.STRENGTH bounds."""
        if slug in self.connections:
            min_strength, max_strength = RelationshipConstants.STRENGTH
            strength = max(min_strength, min(new_strength, max_strength))
            self.connections[slug].strength = strength
            self._event_bus.publish(
                "relationship_strength_updated",
                slug=slug,
                strength=strength,
                connection=self.connections[slug],
            )

    def get_connection(self, slug: str) -> Connection | None:
        return self.connections.get(slug)

    def get_all_connections(self) -> dict[str, Connection]:
        return self.connections

    def update_connection_decay_rate(
        self, slug: str, new_decay_rate: float
    ) -> None:
        if slug in self.connections:
            decay_rate = max(0.0, new_decay_rate)
            self.connections[slug].decay_rate = decay_rate
            self._event_bus.publish(
                "relationship_decay_rate_updated",
                slug=slug,
                decay_rate=decay_rate,
                connection=self.connections[slug],
            )

    def update_connection_decay_threshold(
        self, slug: str, new_decay_threshold: int
    ) -> None:
        if slug in self.connections:
            self.connections[slug].decay_threshold = new_decay_threshold
            self._event_bus.publish(
                "relationship_decay_threshold_updated",
                slug=slug,
                decay_threshold=new_decay_threshold,
                connection=self.connections[slug],
            )


def encode_relationships(relationships: Relationships) -> Mapping[str, Any]:
    """Encodes a Relationships object to a dictionary."""
    return {
        slug: entry.get_state()
        for slug, entry in relationships.connections.items()
    }


def decode_relationships(
    json_data: Mapping[str, Any], event_bus: EventBus
) -> Relationships:
    """Decodes a dictionary to a Relationships object."""
    relationships = Relationships(event_bus)
    if json_data:
        for slug, entry_data in json_data.items():
            connection = Connection(**entry_data)
            relationships.connections[slug] = connection
    return relationships
