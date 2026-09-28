# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon.database.rules import config_monster

if TYPE_CHECKING:
    from tuxemon.db import Acquisition, EvolutionStage


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
        self._bond: int = config_monster.starting_bond
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

    def increase_bond(self, amount: int) -> set[int]:
        """Increases bond by a given amount. Returns newly crossed milestones."""
        previous = self.bond
        self.bond += amount
        milestones = set(config_monster.bond_milestones)
        return {m for m in milestones if previous < m <= self.bond}

    def decrease_bond(self, amount: int, floor: int | None = None) -> None:
        """Decreases bond by a given amount, respecting an optional floor."""
        self.bond = self._floored_decrease(amount, floor)

    def _floored_decrease(self, amount: int, floor: int | None) -> int:
        """
        Returns the bond left after subtracting ``amount``, clamped to a floor.

        A floor above the current bond only stops the drop, it never raises
        bond, so a penalty can't reward a monster sitting under its floor.
        """
        effective_floor = floor if floor is not None else self.MIN_BOND
        return min(self.bond, max(effective_floor, self.bond - amount))

    def reset_bond(self) -> None:
        """Resets bond to default value."""
        self.bond = config_monster.starting_bond

    def bond_decay(
        self, decay_rate: float = 0.05, floor: int | None = None
    ) -> None:
        """Applies passive bond decay, stopping at floor or MIN_BOND."""
        effective_floor = floor if floor is not None else self.MIN_BOND
        if self.bond <= effective_floor:
            return
        decay_amount = max(1, int(self.bond * decay_rate))
        self.bond = self._floored_decrease(decay_amount, floor)

    def change_bond(
        self, value: int | float, floor: int | None = None
    ) -> set[int]:
        """Adjusts bond by an absolute amount or a percentage of current bond."""
        bond_change = (
            int(value * self.bond) if isinstance(value, float) else value
        )
        if bond_change > 0:
            return self.increase_bond(bond_change)
        elif bond_change < 0:
            self.decrease_bond(abs(bond_change), floor)
        return set()

    def is_max_bond(self) -> bool:
        return self.bond >= self.MAX_BOND

    def is_low_bond(self, threshold: int = 20) -> bool:
        return self.bond <= threshold

    def _get_sentiment_key(self) -> str | None:
        for key, (
            min_bond,
            max_bond,
        ) in config_monster.bond_sentiments.items():
            if min_bond <= self.bond <= max_bond:
                return key
        return None

    def get_bond_sentiment(
        self, monster_name: str, player_name: str
    ) -> str | None:
        """
        Returns the msgid corresponding to the current bond level,
        based on the configured bond_sentiments dictionary.
        """
        key = self._get_sentiment_key()
        if key:
            template = config_monster.bond_strings.get(key)
            if template:
                return template.format(
                    monster_name=monster_name, player_name=player_name
                )
        return None

    def get_bond_icon_path(self) -> str | None:
        """
        Returns the file path to the bond icon based on the monster's current bond level.
        """
        key = self._get_sentiment_key()
        return config_monster.bond_icons.get(key) if key else None

    def apply_bond_modifier(self, event: str) -> set[int]:
        """Applies a bond change based on a named event."""
        modifier = config_monster.bond_modifiers.get(event)
        if modifier is not None:
            return self.change_bond(modifier)
        return set()

    def get_effective_min_bond(self, stage: EvolutionStage) -> int:
        """Returns the minimum bond floor for the given evolution stage."""
        stage_floors = config_monster.bond_stage_floors
        return stage_floors.get(stage.value, self.MIN_BOND)

    def set_bond_for_acquisition(self, acquisition: Acquisition) -> None:
        """Sets starting bond based on how the monster was acquired."""
        bond_acquisition = config_monster.bond_acquisition
        self.bond = bond_acquisition.get(
            acquisition.value, config_monster.starting_bond
        )
