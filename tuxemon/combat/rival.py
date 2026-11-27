# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
The rival: a pay-to-win foil who challenges the player in contests.

Pure helpers (no game state) so contests can be tuned and tested:

* which monsters the rival "buys" (species strong against the player's),
* the contests: highest stat (breeder), rarest monster (researcher),
  biggest haul on a route (collector), and the rival's battle team (gym).

Tuning is deliberately simple for fun-testing.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

# Stats the breeder may ask for ("put forward your strongest/fastest").
CONTEST_STATS = ("melee", "ranged", "armour", "dodge", "speed")
# The collector's route race: how many encounters each side gets, and the
# rival's haul (new species found), drawn at random in this range.
COLLECT_ENCOUNTERS = 5
RIVAL_HAUL = (1, 3)
# The rival's battle monsters are the player's level divided by this,
# rounded down, never below 1.
LEVEL_DIVISOR = 2


# The monster Rex shows off in the keeper's bet is freshly bought: always
# this level, whatever the player's. Level barely moves a stat this low
# (a level-1 Nebufin out-dodged a level-5 Agnite, 79 to 72), so its stat is
# also divided by SHOW_DIVISOR: a newborn that has not grown into itself.
# Easy on purpose for now: the player always wins.
SHOW_LEVEL = 1
SHOW_DIVISOR = 10


def show_stat(value: float) -> int:
    """The stat of Rex's show monster as the bet counts it (at least 1)."""
    return max(1, int(value) // SHOW_DIVISOR)


@dataclass(frozen=True)
class Species:
    slug: str
    types: tuple[str, ...]
    catch_rate: float


def rarity(catch_rate: float) -> int:
    """Rarity score: harder to catch = rarer. 0 (common) and up."""
    return max(0, round(100 - catch_rate))


def counters(
    defend: str, chart: Mapping[str, Mapping[str, float]]
) -> set[str]:
    """Attack types that do more than normal damage to `defend`.

    chart[attack][defend] is the multiplier (missing = 1).
    """
    return {a for a, row in chart.items() if row.get(defend, 1.0) > 1.0}


def counter_species(
    target_types: Sequence[str],
    pool: Iterable[Species],
    chart: Mapping[str, Mapping[str, float]],
    rng: random.Random,
) -> Species:
    """A species strong against the target's first type (any, if none is)."""
    pool = list(pool)
    good = counters(target_types[0], chart) if target_types else set()
    picks = [s for s in pool if good.intersection(s.types)] or pool
    return rng.choice(picks)


def outcome(you: float, rival: float) -> str:
    if you > rival:
        return "win"
    if you < rival:
        return "lose"
    return "draw"


def rival_level(level: int, rng: random.Random) -> int:
    return max(1, level // LEVEL_DIVISOR)


def rival_team(
    party: Sequence[tuple[Sequence[str], int]],
    pool: Iterable[Species],
    chart: Mapping[str, Mapping[str, float]],
    rng: random.Random,
    size: int = 1,
    level: int | None = None,
) -> list[tuple[str, int]]:
    """The rival's battle team: one counter per player monster (types, level),
    for the first `size` of the player's team, at about half the level.

    If `level` is given, every monster on the team has exactly that level
    (clamped to at least 1), ignoring the player's levels.  Otherwise each
    monster's level is derived from the corresponding player monster via
    `rival_level`.
    """
    pool = list(pool)
    if level is not None:
        fixed = max(1, level)
        return [
            (counter_species(types, pool, chart, rng).slug, fixed)
            for types, _ in party[:size]
        ]
    return [
        (
            counter_species(types, pool, chart, rng).slug,
            rival_level(mon_level, rng),
        )
        for types, mon_level in party[:size]
    ]
