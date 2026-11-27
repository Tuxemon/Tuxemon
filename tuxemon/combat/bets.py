# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Bets: small contests a temple's pupil challenges the player to.

"I bet you have never seen a monster taller than 10 cm" - the player shows
one from the Tuxepedia. "I bet none of yours can lift this rock" - the player
puts forward a monster from the team; the bar is not told.

Pure helpers (no game state), so the rules can be tested and tuned.
"""

from __future__ import annotations

WIN, LOSE, NONE = "win", "lose", "none"
# Team stats a bet may ask for.
BET_STATS = (
    "melee",
    "ranged",
    "armour",
    "dodge",
    "speed",
    "level",
    "weight",
    "height",
)
CM_PER_FOOT = 30.48
LB_PER_KG = 2.20462


def taller_than(height_cm: float, bar_cm: float) -> str:
    """The Tuxepedia bet: win only if strictly taller than the bar."""
    return WIN if height_cm > bar_cm else LOSE


def strong_enough(value: float, bar: float) -> str:
    """The team bet: win if the stat reaches the (untold) bar."""
    return WIN if value >= bar else LOSE


def weight_text(weight_kg: float, unit: str = "metric") -> str:
    """'1.5 kg', or '3.3 lb' when the game is set to imperial."""
    if unit != "metric":
        return f"{weight_kg * LB_PER_KG:.1f} lb"
    return f"{weight_kg:.1f} kg"


def value_text(stat: str, value: float, unit: str = "metric") -> str:
    """A team monster's stat as the bet's dialog shows it."""
    if stat == "weight":
        return weight_text(value, unit)
    if stat == "height":
        return height_text(value, unit)
    return str(value)


def height_text(height_cm: float, unit: str = "metric") -> str:
    """'12 cm', '2.5 m', or '3 ft' when the game is set to imperial."""
    if unit != "metric":
        return f"{round(height_cm / CM_PER_FOOT)} ft"
    if height_cm >= 100:
        return f"{height_cm / 100:.1f} m"
    return f"{round(height_cm)} cm"
