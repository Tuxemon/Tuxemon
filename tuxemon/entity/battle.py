# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from tuxemon.battle import Battle, decode_battle, encode_battle
from tuxemon.db import OutputBattle

if TYPE_CHECKING:
    from tuxemon.save_system.save_state import NPCState

logger = logging.getLogger(__name__)

LEGACY_PLACEHOLDER = "player"


class BattlesHandler:
    """Manages a collection of battles for a specific character."""

    def __init__(
        self,
        character: str = "player",
        initial_battles: list[Battle] | None = None,
    ) -> None:
        self.character = character
        self._battles = initial_battles if initial_battles is not None else []

    def record_battle(
        self,
        opponent: str,
        outcome: OutputBattle,
        location: str = "",
        turns: int = 1,
    ) -> Battle:
        """Records a new battle and adds it to the history."""
        data = {
            "fighter": self.character,
            "opponent": opponent,
            "outcome": outcome,
            "timestamp": time.time(),
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

    def get_last_battle(self) -> Battle | None:
        """Returns the most recent battle, if any."""
        if self._battles:
            return self._battles[-1]
        return None

    def get_last_battle_outcome(self, opponent: str) -> str | None:
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

        average_turns = (
            sum(b.turns for b in self._battles) / len(self._battles)
            if self._battles
            else 0.0
        )

        return {
            "total": total_battles,
            "won": battle_outcomes[OutputBattle.WON],
            "lost": battle_outcomes[OutputBattle.LOST],
            "draw": battle_outcomes[OutputBattle.DRAW],
            "average_turns": round(average_turns),
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

    def decode_battle(self, json_data: NPCState | None) -> None:
        """Deserializes and loads battles from saved data."""
        if json_data is None or json_data.battles is None:
            return

        decoded = decode_battle(json_data.battles)

        for battle in decoded:
            if battle.fighter == LEGACY_PLACEHOLDER:
                battle.fighter = self.character
            if battle.opponent == LEGACY_PLACEHOLDER:
                battle.opponent = self.character

        self._battles = decoded
