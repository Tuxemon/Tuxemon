# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster


@dataclass
class DamageReport:
    attack: Monster
    defense: Monster
    damage: int
    turn: int

    def __repr__(self) -> str:
        return (
            f"DamageReport(attack={self.attack}, defense={self.defense}, "
            f"damage={self.damage}, turn={self.turn})"
        )


class DamageTracker:
    def __init__(self) -> None:
        self._damage_map: dict[
            tuple[Monster, Monster], list[DamageReport]
        ] = {}

    def log_damage(
        self, attacker: Monster, defender: Monster, damage: int, turn: int
    ) -> None:
        """
        Log a damage event into the damage map.
        """
        key = (attacker, defender)
        if key not in self._damage_map:
            self._damage_map[key] = []
        self._damage_map[key].append(
            DamageReport(attacker, defender, damage, turn)
        )

    def get_damages(
        self, attacker: Monster, defender: Monster
    ) -> list[DamageReport]:
        """
        Retrieve all damage reports for a specific pair of attacker
        and defender.
        """
        key = (attacker, defender)
        return self._damage_map.get(key, [])

    def remove_monster(self, monster: Monster) -> None:
        """
        Remove all damage reports involving the given monster.
        """
        self._damage_map = {
            key: reports
            for key, reports in self._damage_map.items()
            if key[0] != monster and key[1] != monster
        }

    def clear_damage(self) -> None:
        """
        Clear all damage reports.
        """
        self._damage_map.clear()

    def get_all_damages(self) -> list[DamageReport]:
        """
        Flatten and retrieve all recorded damage reports as a single list.
        """
        return [
            report
            for reports in self._damage_map.values()
            for report in reports
        ]

    def get_attackers(self, loser: Monster) -> set[Monster]:
        """
        Retrieve all monsters who attacked the given target (loser).
        """
        attackers = set()
        for reports in self._damage_map.values():
            for report in reports:
                if report.defense == loser:
                    attackers.add(report.attack)
        return attackers

    def count_hits(
        self, loser: Monster, winner: Monster | None = None
    ) -> tuple[int, int]:
        """
        Count the number of hits on the loser and optionally the hits
        by a specific winner.
        """
        total_hits = 0
        winner_hits = 0
        for reports in self._damage_map.values():
            for report in reports:
                if report.defense == loser:
                    total_hits += 1
                    if winner and report.attack == winner:
                        winner_hits += 1
        return total_hits, winner_hits

    def total_damage_by_attacker(self, attacker: Monster) -> int:
        """
        Calculate the total damage dealt by a specific attacker.
        """
        return sum(
            report.damage
            for reports in self._damage_map.values()
            for report in reports
            if report.attack == attacker
        )

    def __repr__(self) -> str:
        return (
            f"DamageTracker with {len(self.get_all_damages())} entries. "
            f"Attackers: {set(report.attack for report in self.get_all_damages())}"
        )
