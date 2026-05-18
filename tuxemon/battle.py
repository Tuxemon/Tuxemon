# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID, uuid4

from tuxemon.db import OutputBattle

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "fighter",
    "opponent",
    "outcome",
    "timestamp",
    "location",
    "turns",
)


class Battle:
    """Represents a single battle instance between two characters."""

    def __init__(self) -> None:
        self.instance_id: UUID = uuid4()
        self.fighter: str = ""
        self.opponent: str = ""
        self.outcome: OutputBattle = OutputBattle.DRAW
        self.timestamp: float = time.time()
        self.location: str = ""
        self.turns: int = 1

    @classmethod
    def from_save_data(cls, save_data: Mapping[str, Any]) -> Battle:
        """Creates a Battle instance from saved data."""
        battle = cls()

        if "instance_id" in save_data and save_data["instance_id"]:
            battle.instance_id = UUID(save_data["instance_id"])

        for key in SIMPLE_PERSISTANCE_ATTRIBUTES:
            if key in save_data:
                setattr(battle, key, save_data[key])

        return battle

    def get_state(self) -> Mapping[str, Any]:
        """Returns a dictionary representing the current battle state."""
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = self.instance_id.hex

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """Updates the battle state from saved data."""
        if not save_data:
            return

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_battle(
    json_data: Sequence[Mapping[str, Any]] | None,
) -> list[Battle]:
    """Converts saved battle data into Battle instances."""
    return [Battle.from_save_data(battle) for battle in (json_data or [])]


def encode_battle(battles: Sequence[Battle]) -> Sequence[Mapping[str, Any]]:
    """Converts Battle instances into savable dictionaries."""
    return [battle.get_state() for battle in battles]
