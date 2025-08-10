# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Optional
from uuid import UUID, uuid4

from tuxemon.db import OutputBattle

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "fighter",
    "opponent",
    "outcome",
    "steps",
    "location",
    "turns",
)
LEGACY_PLACEHOLDER = "player"


class Battle:
    """Represents a single battle instance between two characters."""

    def __init__(self) -> None:
        self.instance_id: UUID = uuid4()
        self.fighter: str = ""
        self.opponent: str = ""
        self.outcome: OutputBattle = OutputBattle.draw
        self.steps: int = 1
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


class BattlesHandler:
    """Manages a collection of battles for a specific character."""

    def __init__(
        self,
        character: str = "player",
        initial_battles: Optional[list[Battle]] = None,
    ) -> None:
        self.character = character
        self._battles = initial_battles if initial_battles is not None else []

    def record_battle(
        self,
        opponent: str,
        outcome: OutputBattle,
        steps: int,
        location: str = "",
        turns: int = 1,
    ) -> Battle:
        """Records a new battle and adds it to the history."""
        data = {
            "fighter": self.character,
            "opponent": opponent,
            "outcome": outcome,
            "steps": steps,
            "location": location,
            "turns": turns,
        }
        battle = Battle.from_save_data(data)
        self.add_battle(battle)
        return battle

    def add_battle(self, battle: Battle) -> None:
        """Adds a battle to the internal battle list."""
        self._battles.append(battle)

    def get_battles(self) -> list[Battle]:
        """Returns all recorded battles."""
        return list(self._battles)

    def clear_battles(self) -> None:
        """Removes all recorded battles."""
        self._battles.clear()

    def has_fought_and_outcome(self, outcome: str, opponent: str) -> bool:
        """Checks if a battle with a specific outcome against an opponent exists."""
        try:
            expected_outcome = OutputBattle(outcome)
        except ValueError:
            logger.error(f"'{outcome}' isn't a valid battle outcome.")
            return False

        for battle in reversed(self._battles):
            if (
                battle.fighter == self.character
                and battle.opponent == opponent
                and battle.outcome == expected_outcome
            ):
                return True

        return False

    def get_last_battle(self) -> Optional[Battle]:
        """Returns the most recent battle, if any."""
        if self._battles:
            return self._battles[-1]
        return None

    def get_last_battle_outcome(self, opponent: str) -> Optional[str]:
        """Returns the outcome of the last battle against a specific opponent."""
        for battle in reversed(self._battles):
            if (
                battle.fighter == self.character
                and battle.opponent == opponent
            ):
                return battle.outcome.value
        return None

    def get_battle_outcome_stats(self) -> dict[OutputBattle, int]:
        """Returns a count of each battle outcome for the character."""
        battle_outcomes = {outcome: 0 for outcome in OutputBattle}

        for battle in self._battles:
            if battle.fighter == self.character:
                battle_outcomes[battle.outcome] += 1

        return battle_outcomes

    def get_battle_outcome_summary(self) -> dict[str, int]:
        """Returns a summary of total battles and outcomes."""
        battle_outcomes = self.get_battle_outcome_stats()
        total_battles = sum(battle_outcomes.values())

        return {
            "total": total_battles,
            "won": battle_outcomes[OutputBattle.won],
            "lost": battle_outcomes[OutputBattle.lost],
            "draw": battle_outcomes[OutputBattle.draw],
            "average_turns": sum(b.turns for b in self._battles)
            // len(self._battles),
        }

    def get_battles_by_location(self) -> dict[str, list[Battle]]:
        """Groups battles by location and returns them as a dictionary."""
        locations: dict[str, list[Battle]] = {}
        for battle in self._battles:
            loc = battle.location
            locations.setdefault(loc, []).append(battle)
        return locations

    def encode_battle(self) -> Sequence[Mapping[str, Any]]:
        """Serializes battles into a savable format."""
        return encode_battle(self._battles)

    def decode_battle(self, json_data: Optional[Mapping[str, Any]]) -> None:
        """Deserializes and loads battles from saved data."""
        if json_data and "battles" in json_data:
            decoded = decode_battle(json_data["battles"])

            for battle in decoded:
                if battle.fighter == LEGACY_PLACEHOLDER:
                    battle.fighter = self.character
                if battle.opponent == LEGACY_PLACEHOLDER:
                    battle.opponent = self.character

            self._battles = decoded


def decode_battle(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Battle]:
    """Converts saved battle data into Battle instances."""
    return [Battle.from_save_data(battle) for battle in json_data or []]


def encode_battle(battles: Sequence[Battle]) -> Sequence[Mapping[str, Any]]:
    """Converts Battle instances into savable dictionaries."""
    return [battle.get_state() for battle in battles]
