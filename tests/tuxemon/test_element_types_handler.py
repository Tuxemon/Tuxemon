# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.database.runtime import db
from tuxemon.db import ElementModel
from tuxemon.element import Element, ElementTypesHandler


@pytest.fixture
def elements():
    fire = ElementModel(
        slug="fire", icon="gfx/ui/icons/element/fire_type.png", types=[]
    )
    metal = ElementModel(
        slug="metal", icon="gfx/ui/icons/element/metal_type.png", types=[]
    )
    aether = ElementModel(
        slug="aether", icon="gfx/ui/icons/element/aether_type.png", types=[]
    )

    db.database["element"] = {
        "fire": fire,
        "metal": metal,
        "aether": aether,
    }

    return {
        "fire": Element.get("fire"),
        "metal": Element.get("metal"),
        "aether": Element.get("aether"),
    }


@pytest.fixture
def handler(elements):
    return ElementTypesHandler(["metal", "fire"])


def test_init_with_no_types():
    basic = ElementTypesHandler()
    assert basic.current == []
    assert basic.default == []


def test_init_with_types(handler):
    assert len(handler.current) == 2
    assert len(handler.default) == 2


def test_set_types(elements):
    basic = ElementTypesHandler()
    basic.set_types(["fire", "metal"])
    assert basic.get_type_slugs() == ["fire", "metal"]


def test_reset_to_default(handler):
    handler.set_types(["metal"])
    handler.reset_to_default()
    assert handler.get_type_slugs() == ["metal", "fire"]


def test_get_type_slugs(handler):
    assert handler.get_type_slugs() == ["metal", "fire"]


def test_has_type(handler):
    assert handler.has_type("metal")
    assert not handler.has_type("non_existent_type")


def test_primary_type(handler):
    assert handler.primary.slug == "metal"
    assert handler.primary is not None


@pytest.mark.parametrize(
    "attackers, defenders, expected_fn",
    [
        pytest.param(
            ["fire"],
            ["metal"],
            lambda e: e["fire"].lookup_multiplier("metal"),
            id="fire_vs_metal",
        ),
        pytest.param(
            ["metal"],
            ["fire"],
            lambda e: e["metal"].lookup_multiplier("fire"),
            id="metal_vs_fire",
        ),
        pytest.param(
            ["fire", "metal"],
            ["fire", "metal"],
            lambda e: (
                e["fire"].lookup_multiplier("fire")
                * e["fire"].lookup_multiplier("metal")
                * e["metal"].lookup_multiplier("fire")
                * e["metal"].lookup_multiplier("metal")
            ),
            id="dual_vs_dual",
        ),
        pytest.param(
            ["fire", "aether"],
            ["metal"],
            lambda e: e["fire"].lookup_multiplier("metal"),
            id="aether_ignored_fire_vs_metal",
        ),
    ],
)
def test_calculate_affinity_score(elements, attackers, defenders, expected_fn):
    atk = [elements[a] for a in attackers]
    dfn = [elements[d] for d in defenders]
    score = ElementTypesHandler.calculate_affinity_score(atk, dfn)
    assert score == expected_fn(elements)


@pytest.mark.parametrize(
    "defenders, attacker, expected_fn",
    [
        pytest.param(
            ["metal"],
            "fire",
            lambda e: e["metal"].lookup_multiplier("fire"),
            id="metal_resists_fire",
        ),
        pytest.param(
            ["fire", "metal"],
            "fire",
            lambda e: (
                e["fire"].lookup_multiplier("fire")
                * e["metal"].lookup_multiplier("fire")
            ),
            id="dual_defenders_fire_attacker",
        ),
        pytest.param(
            ["aether", "fire"],
            "metal",
            lambda e: e["fire"].lookup_multiplier("metal"),
            id="aether_ignored_fire_vs_metal",
        ),
        pytest.param(
            ["fire", "metal"],
            "aether",
            lambda e: 1.0,
            id="aether_neutral",
        ),
    ],
)
def test_resistance(elements, defenders, attacker, expected_fn):
    dfn = [elements[d] for d in defenders]
    score = ElementTypesHandler.calculate_resistance_multiplier_for_types(
        dfn, attacker
    )
    assert score == expected_fn(elements)


def test_lookup_multiplier_missing_entry(elements):
    fire = elements["fire"]
    assert fire.lookup_multiplier("nonexistent") == 1.0


def test_set_types_with_unknown_slug():
    handler = ElementTypesHandler()
    handler.set_types(["unknown_slug"])
    assert handler.get_type_slugs() == ["unknown_slug"]
    elem = Element.get("unknown_slug")
    assert elem.slug == "unknown_slug"
    assert elem.types == []


def test_primary_raises_on_empty():
    handler = ElementTypesHandler()
    with pytest.raises(ValueError):
        _ = handler.primary


def test_affinity_aether_user(elements):
    atk = [elements["aether"]]
    dfn = [elements["fire"]]
    score = ElementTypesHandler.calculate_affinity_score(atk, dfn)
    assert score == 1.0


def test_affinity_aether_target(elements):
    atk = [elements["fire"]]
    dfn = [elements["aether"]]
    score = ElementTypesHandler.calculate_affinity_score(atk, dfn)
    assert score == 1.0


def test_resistance_aether_defender(elements):
    dfn = [elements["aether"]]
    score = ElementTypesHandler.calculate_resistance_multiplier_for_types(
        dfn, "fire"
    )
    assert score == 1.0


def test_resistance_aether_attacker(elements):
    dfn = [elements["fire"]]
    score = ElementTypesHandler.calculate_resistance_multiplier_for_types(
        dfn, "aether"
    )
    assert score == 1.0


def test_element_get_uses_cache(elements):
    fire1 = Element.get("fire")
    fire2 = Element.get("fire")
    assert fire1 is fire2


def test_element_cache_clears(elements):
    fire1 = Element.get("fire")
    Element.clear_cache()
    fire2 = Element.get("fire")
    assert fire1 is not fire2


def test_multiplier_cache_reuse(elements):
    ElementTypesHandler.clear_cache()

    score1 = ElementTypesHandler.calculate_affinity_score(
        [elements["fire"]], [elements["metal"]]
    )
    assert ("fire", "metal") in ElementTypesHandler._multiplier_cache

    old_value = ElementTypesHandler._multiplier_cache[("fire", "metal")]
    elements["fire"].lookup_multiplier = lambda slug: 9999

    score2 = ElementTypesHandler.calculate_affinity_score(
        [elements["fire"]], [elements["metal"]]
    )

    assert score2 == old_value


def test_element_name_translation(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.locale.locale.T.translate", lambda slug: f"X_{slug}"
    )
    elem = Element.get("fire")
    assert elem.name == "X_fire"


def test_element_name_empty_slug(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.locale.locale.T.translate", lambda slug: f"X_{slug}"
    )
    elem = Element("", "", [])
    assert elem.name == ""


def test_reset_to_default_mixed_slugs(elements):
    handler = ElementTypesHandler(["fire", "metal"])
    handler.set_types(["aether"])
    handler.reset_to_default()
    assert handler.get_type_slugs() == ["fire", "metal"]


def test_ordering_preserved_in_current(elements):
    handler = ElementTypesHandler(["fire", "metal"])
    assert handler.get_type_slugs() == ["fire", "metal"]


def test_ordering_preserved_after_set_types(elements):
    handler = ElementTypesHandler(["metal", "fire"])
    handler.set_types(["aether", "fire"])
    assert handler.get_type_slugs() == ["aether", "fire"]


def test_ordering_preserved_after_reset(elements):
    handler = ElementTypesHandler(["fire", "metal"])
    handler.set_types(["metal"])
    handler.reset_to_default()
    assert handler.get_type_slugs() == ["fire", "metal"]


def test_affinity_multi_type_with_aether(elements):
    Element.clear_cache()
    elements = {
        "fire": Element.get("fire"),
        "metal": Element.get("metal"),
        "aether": Element.get("aether"),
    }

    atk = [elements["aether"], elements["fire"]]
    dfn = [elements["metal"]]
    score = ElementTypesHandler.calculate_affinity_score(atk, dfn)

    assert score == 1.0


def test_resistance_multi_type_with_aether(elements):
    Element.clear_cache()
    elements = {
        "fire": Element.get("fire"),
        "metal": Element.get("metal"),
        "aether": Element.get("aether"),
    }

    dfn = [elements["aether"], elements["fire"]]
    score = ElementTypesHandler.calculate_resistance_multiplier_for_types(
        dfn, "metal"
    )

    assert score == 1.0


def test_affinity_aether_in_middle(elements):
    atk = [elements["fire"], elements["aether"], elements["metal"]]
    dfn = [elements["fire"]]
    score = ElementTypesHandler.calculate_affinity_score(atk, dfn)
    expected = elements["fire"].lookup_multiplier("fire") * elements[
        "metal"
    ].lookup_multiplier("fire")
    assert score == expected


def test_resistance_aether_in_middle(elements):
    dfn = [elements["fire"], elements["aether"], elements["metal"]]
    score = ElementTypesHandler.calculate_resistance_multiplier_for_types(
        dfn, "fire"
    )
    expected = elements["fire"].lookup_multiplier("fire") * elements[
        "metal"
    ].lookup_multiplier("fire")
    assert score == expected
