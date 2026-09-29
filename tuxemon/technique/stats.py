# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TechniqueBaseStats:
    """
    The immutable, base statistical attributes loaded from the database.
    (The Source of Truth/Defaults).
    """

    accuracy: float = 0.0
    potency: float = 0.0
    power: float = 1.0
    healing_power: float = 0.0


@dataclass
class TechniqueCustomBoosts:
    """
    Persistent, user- or modder-defined additive boosts to technique stats.
    (Loaded from the Save File).
    """

    power: float = 0.0
    potency: float = 0.0
    accuracy: float = 0.0
    healing_power: float = 0.0

    def to_dict(self) -> Mapping[str, Any]:
        """Convert boosts to a dict for saving."""
        return {
            "accuracy_boost": self.accuracy,
            "potency_boost": self.potency,
            "power_boost": self.power,
            "healing_power_boost": self.healing_power,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TechniqueCustomBoosts:
        """Create boosts from loaded dict."""
        return cls(
            accuracy=data.get("accuracy_boost", 0.0),
            potency=data.get("potency_boost", 0.0),
            power=data.get("power_boost", 0.0),
            healing_power=data.get("healing_power_boost", 0.0),
        )


@dataclass
class TechniqueCurrentStats:
    """
    The current, dynamic statistical attributes that can be modified in battle.
    (Reset to Base + Boosts outside of battle).
    """

    potency: float = 0.0
    accuracy: float = 0.0
    power: float = 0.0
    healing_power: float = 0.0
