# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from tuxemon.db import OutputBattle

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "fighter",
    "opponent",
    "outcome",
    "steps",
)


class Battle:
    """
    Tuxemon Battle.
    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id = uuid.uuid4()
        self.fighter = ""
        self.opponent = ""
        self.outcome = OutputBattle.draw
        self.steps = 0

        self.set_state(save_data)

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the battle to be saved to a file.

        Returns:
            Dictionary containing all the information about the battle.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        Parameters:
            save_data: Data used to reconstruct the battle.

        """
        if not save_data:
            return

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_battle(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Battle]:
    return [Battle(save_data=battle) for battle in json_data or {}]


def encode_battle(battles: Sequence[Battle]) -> Sequence[Mapping[str, Any]]:
    return [battle.get_state() for battle in battles]
