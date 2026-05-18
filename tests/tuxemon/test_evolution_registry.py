# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from uuid import UUID

import pytest

from tuxemon.monster.evolution_registry import EvolutionRegistry


@pytest.fixture
def registry():
    logging.basicConfig(level=logging.DEBUG)
    return EvolutionRegistry()


@pytest.fixture
def monster_id():
    return UUID("123e4567-e89b-12d3-a456-426655440000")


@pytest.fixture
def slug():
    return "slug"


@pytest.fixture
def level():
    return 1


def test_log_missed(registry, monster_id, slug, level):
    registry.log_missed(monster_id, slug, level)
    missed = registry._missed_evolutions[monster_id]
    assert len(missed) == 1
    assert missed[0].slug == slug
    assert missed[0].level == level
    assert missed[0].count == 1


def test_log_missed_increment(registry, monster_id, slug, level):
    registry.log_missed(monster_id, slug, level)
    registry.log_missed(monster_id, slug, level)
    missed = registry._missed_evolutions[monster_id]
    assert len(missed) == 1
    assert missed[0].count == 2


import pytest


@pytest.mark.parametrize(
    "slug,attempts,max_attempts,expected",
    [
        pytest.param("fire", 1, 3, ["fire"], id="below_max_fire"),
        pytest.param("water", 2, 3, ["water"], id="below_max_water"),
        pytest.param("earth", 3, 3, [], id="equal_max_earth"),
        pytest.param("mixed", None, 3, ["fire"], id="mixed_counts"),
    ],
)
def test_get_retryable_variants(
    registry, monster_id, level, slug, attempts, max_attempts, expected
):
    if slug == "mixed":
        for _ in range(2):
            registry.log_missed(monster_id, "fire", level)
        for _ in range(4):
            registry.log_missed(monster_id, "water", level)
    else:
        for _ in range(attempts):
            registry.log_missed(monster_id, slug, level)

    retryable = registry.get_retryable_missed(
        monster_id, max_attempts=max_attempts
    )
    assert retryable == expected


def test_clear_missed(registry, monster_id, slug, level):
    registry.log_missed(monster_id, slug, level)
    registry.clear_missed(monster_id)
    assert monster_id not in registry._missed_evolutions


def test_pending_operations(registry, monster_id, slug):
    registry.add_pending(monster_id, slug)
    assert registry.get_pending(monster_id) == [slug]
    registry.clear_pending_slug(monster_id, slug)
    assert registry.get_pending(monster_id) == []
    registry.add_pending(monster_id, slug)
    registry.clear_pending(monster_id)
    assert monster_id not in registry._pending_evolutions


@pytest.mark.parametrize(
    "section,setup,clear_func,get_func,slug1,slug2,expected",
    [
        pytest.param(
            "missed",
            lambda r, mid, lvl, s1, s2: r.decode_registry(
                {
                    "missed": {
                        mid.hex: [
                            {"slug": s1, "level": lvl, "count": 1},
                            {"slug": s2, "level": lvl, "count": 1},
                        ]
                    }
                }
            ),
            lambda r, mid, s: r.clear_missed(mid, s),
            lambda r, mid: [e.slug for e in r._missed_evolutions.get(mid, [])],
            "fire",
            "water",
            ["water"],
            id="missed_clear_first_slug",
        ),
        pytest.param(
            "pending",
            lambda r, mid, lvl, s1, s2: r.decode_registry(
                {"pending": {mid.hex: [s1, s2]}}
            ),
            lambda r, mid, s: r.clear_pending_slug(mid, s),
            lambda r, mid: r.get_pending(mid),
            "fire",
            "water",
            ["water"],
            id="pending_clear_first_slug",
        ),
        pytest.param(
            "missed-nonexistent",
            lambda r, mid, lvl, s1, s2: r.log_missed(mid, s1, lvl),
            lambda r, mid, s: r.clear_missed(mid, s),
            lambda r, mid: [e.slug for e in r._missed_evolutions.get(mid, [])],
            "fire",
            "nonexistent",
            ["fire"],
            id="missed_clear_nonexistent_slug",
        ),
        pytest.param(
            "pending-nonexistent",
            lambda r, mid, lvl, s1, s2: r.add_pending(mid, s1),
            lambda r, mid, s: r.clear_pending_slug(mid, s),
            lambda r, mid: r.get_pending(mid),
            "fire",
            "nonexistent",
            ["fire"],
            id="pending_clear_nonexistent_slug",
        ),
    ],
)
def test_clear_slug_variants(
    registry,
    monster_id,
    level,
    section,
    setup,
    clear_func,
    get_func,
    slug1,
    slug2,
    expected,
):
    setup(registry, monster_id, level, slug1, slug2)
    clear_target = slug2 if "nonexistent" in section else slug1
    clear_func(registry, monster_id, clear_target)
    result = get_func(registry, monster_id)
    assert result == expected


def test_block_unblock(registry, monster_id, slug, level):
    registry.log_missed(monster_id, slug, level)
    registry.block_evolution_forever(monster_id, slug)
    assert slug in registry.get_blocked(monster_id)
    registry.unblock_evolution(monster_id, slug)
    assert slug not in registry.get_blocked(monster_id)


@pytest.mark.parametrize(
    "slugs",
    [
        pytest.param(["fire", "water"], id="two_slugs_fire_water"),
        pytest.param(
            ["fire", "water", "earth"], id="three_slugs_fire_water_earth"
        ),
    ],
)
def test_multiple_slugs(registry, monster_id, level, slugs):
    for s in slugs:
        registry.log_missed(monster_id, s, level)
    missed = registry._missed_evolutions[monster_id]
    assert {evo.slug for evo in missed} == set(slugs)


def test_encode_decode_round_trip(registry, monster_id, slug, level):
    registry.log_missed(monster_id, slug, level)
    registry.add_pending(monster_id, slug)
    registry._blocked_evolutions.setdefault(monster_id, set()).add(slug)

    encoded = registry.encode_registry()
    new_registry = EvolutionRegistry()
    new_registry.decode_registry(encoded)

    assert new_registry._missed_evolutions[monster_id][0].slug == slug
    assert new_registry.get_pending(monster_id) == [slug]
    assert new_registry.get_blocked(monster_id) == {slug}


def test_decode_registry_malformed(registry):
    malformed_data = {
        "missed": {"not-a-uuid": [{"slug": "fire", "level": 1, "count": 1}]},
        "pending": {"also-not-a-uuid": ["water"]},
        "blocked": {"bad-uuid": ["earth"]},
    }
    with pytest.raises(ValueError):
        registry.decode_registry(malformed_data)
