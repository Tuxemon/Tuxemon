# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.database.runtime import db
from tuxemon.db import AttributesModel, ShapeModel
from tuxemon.shape import Shape, ShapeHandler


@pytest.fixture
def shape_models():
    db.database["shape"] = {
        "piscine": ShapeModel(
            slug="piscine",
            attributes=AttributesModel(
                armour=1, dodge=2, hp=3, melee=4, ranged=5, speed=10
            ),
        ),
        "hunter": ShapeModel(
            slug="hunter",
            attributes=AttributesModel(
                armour=10, dodge=1, hp=20, melee=3, ranged=2, speed=1
            ),
        ),
    }
    Shape.clear_cache()
    return db.database["shape"]


def test_shape_get_loads_from_db(shape_models):
    shape = Shape.get("piscine")
    assert shape.slug == "piscine"
    assert shape.attributes.speed == 10


def test_shape_get_uses_cache(shape_models):
    s1 = Shape.get("piscine")
    s2 = Shape.get("piscine")
    assert s1 is s2


def test_shape_fallback_when_missing(shape_models):
    missing = Shape.get("unknown")
    assert missing.slug == "unknown"
    assert missing.attributes.hp == 1  # default fallback


def test_shape_clear_cache(shape_models):
    s1 = Shape.get("piscine")
    Shape.clear_cache()
    s2 = Shape.get("piscine")
    assert s1 is not s2


def test_load_all_shapes(shape_models):
    Shape.clear_cache()
    Shape.load_all_shapes()
    all_shapes = Shape.get_all_shapes()
    assert set(all_shapes.keys()) == {"piscine", "hunter"}


def test_handler_copies_attributes(shape_models):
    handler = ShapeHandler("piscine")
    template = Shape.get("piscine")

    # Must be equal but NOT the same object
    assert handler.attributes.hp == template.attributes.hp
    assert handler.attributes is not template.attributes


def test_handler_slug(shape_models):
    handler = ShapeHandler("hunter")
    assert handler.slug == "hunter"


def test_movement_cost(shape_models):
    handler = ShapeHandler("piscine")
    assert handler.movement_cost(10) == 10 / 10  # speed=10


def test_melee_damage(shape_models):
    handler = ShapeHandler("piscine")
    assert handler.melee_damage(5) == 5 + 4  # melee=4


def test_ranged_damage(shape_models):
    handler = ShapeHandler("piscine")
    assert handler.ranged_damage(5) == 5 + 5  # ranged=5


def test_dodge_chance(shape_models):
    handler = ShapeHandler("piscine")
    assert handler.dodge_chance(0.1) == 0.1 + (2 * 0.02)


def test_armour_reduction(shape_models):
    handler = ShapeHandler("hunter")
    assert handler.armour_reduction(15) == 15 - 10  # armour=10


def test_armour_reduction_never_negative(shape_models):
    handler = ShapeHandler("hunter")
    assert handler.armour_reduction(5) == 0


def test_apply_modifier_changes_local_only(shape_models):
    handler = ShapeHandler("piscine")
    template = Shape.get("piscine")

    handler.apply_modifier(speed=+5, melee=-2)

    assert handler.attributes.speed == template.attributes.speed + 5
    assert handler.attributes.melee == template.attributes.melee - 2

    # Template must remain unchanged
    assert template.attributes.speed == 10
    assert template.attributes.melee == 4


def test_apply_modifier_ignores_unknown_fields(shape_models):
    handler = ShapeHandler("piscine")
    handler.apply_modifier(nonexistent=10)
    assert True


def test_default_shape_when_none_provided(shape_models):
    handler = ShapeHandler(None)
    assert handler.slug == "default"
    assert handler.attributes.hp == 1
