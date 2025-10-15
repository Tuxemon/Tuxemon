# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, Union

from tuxemon import prepare
from tuxemon.formula import config_monster


class BondHandler:
    """
    Handles the bond level of a Tuxemon monster.

    This class encapsulates logic for managing a monster's bond, including
    persistence, modification, and decay over time or due to events.
    """

    MAX_BOND = config_monster.bond_range[1]
    MIN_BOND = config_monster.bond_range[0]

    def __init__(self, save_data: Mapping[str, Any] | None = None) -> None:
        save_data = save_data or {}
        self._bond: int = prepare.BOND
        self.set_state(save_data)

    @property
    def bond(self) -> int:
        """Public getter for bond value."""
        return self._bond

    @bond.setter
    def bond(self, value: int) -> None:
        """Public setter with clamping logic."""
        self._bond = max(self.MIN_BOND, min(value, self.MAX_BOND))

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """Loads bond value from saved data, supporting both legacy and nested formats."""
        if "bond_dict" in save_data and isinstance(
            save_data["bond_dict"], dict
        ):
            bond_data = save_data["bond_dict"]
            if "bond" in bond_data:
                self.bond = int(bond_data["bond"])
        elif "bond" in save_data:
            self.bond = int(save_data["bond"])

    def get_state(self) -> dict[str, Any]:
        """Returns bond value in nested format for saving."""
        return {"bond_dict": {"bond": self.bond}}

    def increase_bond(self, amount: int) -> None:
        """Increases bond by a given amount."""
        self.bond += amount

    def decrease_bond(self, amount: int) -> None:
        """Decreases bond by a given amount."""
        self.bond -= amount

    def reset_bond(self) -> None:
        """Resets bond to default value."""
        self.bond = prepare.BOND

    def bond_decay(self, decay_rate: float = 0.05) -> None:
        """Applies passive bond decay."""
        decay_amount = int(self.bond * decay_rate)
        self.decrease_bond(decay_amount)

    def change_bond(self, value: Union[int, float]) -> None:
        """
        Adjusts the bond value using either an absolute or percentage-based input.
        Enforces limits from config_monster.bond_range.
        """
        _minor, _major = config_monster.bond_range
        bond_change = (
            int(value * self.bond) if isinstance(value, float) else value
        )
        new_bond = self.bond + bond_change
        self.bond = max(_minor, min(new_bond, _major))

    def is_max_bond(self) -> bool:
        return self.bond >= self.MAX_BOND

    def is_low_bond(self, threshold: int = 20) -> bool:
        return self.bond <= threshold

    def get_bond_sentiment(
        self, monster_name: str, player_name: str
    ) -> Optional[str]:
        """
        Returns the msgid corresponding to the current bond level,
        based on the configured bond_sentiments dictionary.
        """
        bond_level = self.bond
        bond_sentiments = config_monster.bond_sentiments
        bond_strings = config_monster.bond_strings

        for sentiment_key, (min_bond, max_bond) in bond_sentiments.items():
            if min_bond <= bond_level <= max_bond:
                sentence_template = bond_strings.get(sentiment_key)
                if sentence_template:
                    return sentence_template.format(
                        monster_name=monster_name, player_name=player_name
                    )

        return None

    def get_bond_icon_path(self) -> Optional[str]:
        """
        Returns the file path to the bond icon based on the monster's current bond level.
        """
        bond_level = self.bond
        bond_sentiments = config_monster.bond_sentiments
        bond_icons = config_monster.bond_icons

        for sentiment_key, (min_bond, max_bond) in bond_sentiments.items():
            if min_bond <= bond_level <= max_bond:
                return bond_icons.get(sentiment_key)

        return None

    def apply_bond_modifier(self, event: str) -> None:
        """
        Applies a bond change based on a named event using config_monster.bond_modifiers.
        """
        modifier = config_monster.bond_modifiers.get(event)
        if modifier is not None:
            self.change_bond(modifier)
