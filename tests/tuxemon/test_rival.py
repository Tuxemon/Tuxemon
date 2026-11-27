# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random

from tuxemon.combat.rival import (
    COLLECT_ENCOUNTERS,
    CONTEST_STATS,
    LEVEL_DIVISOR,
    RIVAL_HAUL,
    Species,
    counter_species,
    counters,
    outcome,
    rarity,
    rival_level,
    rival_team,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHART = {
    "fire": {"wood": 2.0, "water": 0.5},
    "water": {"fire": 2.0},
    "wood": {"water": 2.0, "fire": 0.5},
}

POOL = [
    Species("embra", ("fire",), 80.0),
    Species("squink", ("water",), 60.0),
    Species("budaye", ("wood",), 45.0),
    Species("rockitten", ("earth",), 70.0),
]


# ---------------------------------------------------------------------------
# 1. rarity
# ---------------------------------------------------------------------------


class TestRarity:
    def test_common(self) -> None:
        assert rarity(100) == 0

    def test_mid(self) -> None:
        assert rarity(45) == 55

    def test_over_100_clamps_to_zero(self) -> None:
        assert rarity(120) == 0

    def test_float_near_100(self) -> None:
        assert rarity(99.6) == 0


# ---------------------------------------------------------------------------
# 2. counters
# ---------------------------------------------------------------------------


class TestCounters:
    def test_wood_countered_by_fire(self) -> None:
        assert counters("wood", CHART) == {"fire"}

    def test_fire_countered_by_water(self) -> None:
        assert counters("fire", CHART) == {"water"}

    def test_earth_has_no_counter(self) -> None:
        assert counters("earth", CHART) == set()


# ---------------------------------------------------------------------------
# 3. counter_species (deterministic pick)
# ---------------------------------------------------------------------------


class TestCounterSpecies:
    def test_wood_target_always_embra(self) -> None:
        for seed in range(20):
            rng = random.Random(seed)
            result = counter_species(("wood",), POOL, CHART, rng)
            assert result.slug == "embra"

    def test_fire_wood_target_uses_first_type(self) -> None:
        for seed in range(20):
            rng = random.Random(seed)
            result = counter_species(("fire", "wood"), POOL, CHART, rng)
            assert result.slug == "squink"


# ---------------------------------------------------------------------------
# 4. counter_species fallback to whole pool
# ---------------------------------------------------------------------------


class TestCounterSpeciesFallback:
    def test_no_counter_earth(self) -> None:
        rng = random.Random(0)
        result = counter_species(("earth",), POOL, CHART, rng)
        assert result.slug in {s.slug for s in POOL}

    def test_empty_target_types(self) -> None:
        rng = random.Random(0)
        result = counter_species((), POOL, CHART, rng)
        assert result.slug in {s.slug for s in POOL}


# ---------------------------------------------------------------------------
# 5. outcome
# ---------------------------------------------------------------------------


class TestOutcome:
    def test_win(self) -> None:
        assert outcome(5, 3) == "win"

    def test_lose(self) -> None:
        assert outcome(3, 5) == "lose"

    def test_draw(self) -> None:
        assert outcome(4, 4) == "draw"


# ---------------------------------------------------------------------------
# 6. rival_level stays in bounds
# ---------------------------------------------------------------------------


class TestRivalLevel:
    def test_exact_levels(self) -> None:
        rng = random.Random(0)
        assert rival_level(10, rng) == 5
        assert rival_level(1, rng) == 1
        assert rival_level(3, rng) == 1
        assert rival_level(40, rng) == 20

    def test_never_below_one(self) -> None:
        rng = random.Random(0)
        for base in (1, 2, 3):
            assert rival_level(base, rng) >= 1


# ---------------------------------------------------------------------------
# 7. rival_team
# ---------------------------------------------------------------------------


class TestRivalTeam:
    PARTY = [
        (("wood",), 10),
        (("fire",), 12),
        (("water",), 8),
        (("wood",), 5),
    ]

    def test_default_size_one(self) -> None:
        rng = random.Random(42)
        team = rival_team(self.PARTY, POOL, CHART, rng)
        assert len(team) == 1
        assert team[0][0] == "embra"
        assert team[0][1] == self.PARTY[0][1] // LEVEL_DIVISOR

    def test_size_three(self) -> None:
        rng = random.Random(42)
        team = rival_team(self.PARTY, POOL, CHART, rng, size=3)
        assert len(team) == 3
        assert [slug for slug, _ in team] == ["embra", "squink", "budaye"]
        for (_, lvl), (_, src_level) in zip(team, self.PARTY):
            assert lvl == max(1, src_level // LEVEL_DIVISOR)

    def test_fixed_level(self) -> None:
        rng = random.Random(42)
        team = rival_team(self.PARTY, POOL, CHART, rng, size=3, level=2)
        assert len(team) == 3
        assert [slug for slug, _ in team] == ["embra", "squink", "budaye"]
        assert all(lvl == 2 for _, lvl in team)

    def test_level_zero_raises_to_one(self) -> None:
        rng = random.Random(42)
        team = rival_team(self.PARTY, POOL, CHART, rng, size=3, level=0)
        assert all(lvl == 1 for _, lvl in team)


# ---------------------------------------------------------------------------
# 8. module constants sanity
# ---------------------------------------------------------------------------


class TestConstants:
    def test_contest_stats_members(self) -> None:
        assert "speed" in CONTEST_STATS
        assert "melee" in CONTEST_STATS

    def test_rival_haul_low_le_high(self) -> None:
        low, high = RIVAL_HAUL
        assert low <= high

    def test_collect_encounters_positive(self) -> None:
        assert COLLECT_ENCOUNTERS > 0


# ---------------------------------------------------------------------------
# 9. Rex's show monster (the keeper's bet) always loses for now
# ---------------------------------------------------------------------------


class TestShowStat:
    def test_divided_and_at_least_one(self) -> None:
        from tuxemon.combat.rival import SHOW_DIVISOR, show_stat

        assert show_stat(79) == 79 // SHOW_DIVISOR
        assert show_stat(3) == 1
        assert show_stat(0) == 1

    def test_any_real_stat_beats_it(self) -> None:
        from tuxemon.combat.rival import show_stat

        # Level-5 stats run from about 40 to about 120.
        assert show_stat(121) < 40
