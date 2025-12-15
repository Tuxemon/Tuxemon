# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import EconomyItemModel, EconomyModel, EconomyMonsterModel
from tuxemon.economy.economy import Economy
from tuxemon.item.item import Item
from tuxemon.monster import Monster


class DummyNPC:
    def __init__(self, variables: dict[str, str]):
        self.game_variables = variables


@pytest.fixture
def economy():
    econ = Economy()
    econ.model = EconomyModel(
        slug="test_economy",
        background="gfx/ui/item/item_menu_bg.png",
        resale_multiplier=0.5,
        items=[
            EconomyItemModel(slug="potion", price=20, cost=5, inventory=10),
            EconomyItemModel(slug="revive", price=100, cost=0),
            EconomyItemModel(slug="tuxeball", price=0, cost=10),
        ],
        monsters=[
            EconomyMonsterModel(
                slug="rockitten", level=5, inventory=1, price=100, cost=50
            ),
            EconomyMonsterModel(
                slug="pairagrin", level=1, inventory=50, price=10, cost=2
            ),
        ],
    )
    econ.refresh_maps()
    return econ


def test_update_item_field_with_valid_item(economy):
    economy.update_entity_field("potion", "item", "price", 30)
    assert economy.get_item("potion").price == 30


def test_update_item_field_with_unknown_item(economy):
    with pytest.raises(RuntimeError):
        economy.update_entity_field("unknown_item", "item", "price", 30)


def test_update_item_quantity_with_valid_item(economy):
    economy.update_item_quantity("potion", 20)
    assert economy.get_item("potion").inventory == 20


def test_update_item_quantity_with_unknown_item(economy):
    with pytest.raises(RuntimeError):
        economy.update_item_quantity("unknown_item", 20)


@pytest.mark.parametrize(
    "slug,expected_level,expected_inventory",
    [
        ("rockitten", 5, 1),
        ("pairagrin", 1, 50),
    ],
)
def test_get_monster_valid(economy, slug, expected_level, expected_inventory):
    monster = economy.get_monster(slug)
    assert monster is not None
    assert monster.level == expected_level
    assert monster.inventory == expected_inventory


def test_get_monster_unknown(economy):
    assert economy.get_monster("unknown_monster") is None


def test_refresh_maps_after_modification(economy):
    new_item = EconomyItemModel(slug="tea", price=200, cost=50, inventory=5)
    economy.model.items.append(new_item)
    assert economy.get_item("tea") is None
    economy.refresh_maps()
    assert economy.get_item("tea").price == 200


@pytest.mark.parametrize(
    "npc_vars,conditions,expected",
    [
        (
            {"quest_stage": "start", "alignment": "good"},
            [{"quest_stage": "start"}, {"alignment": "good"}],
            True,
        ),
        (
            {"quest_stage": "start", "alignment": "evil"},
            [{"quest_stage": "start"}, {"alignment": "good"}],
            False,
        ),
        ({"quest_stage": "middle"}, [{"quest_stage": "start"}], False),
        ({"quest_stage": "start"}, [], True),
    ],
)
def test_variable_conditions(economy, npc_vars, conditions, expected):
    npc = DummyNPC(npc_vars)
    assert economy.variable(conditions, npc) is expected


@pytest.mark.parametrize(
    "entity_cls,slug,kwargs,quantity,seller_mode,expected_price",
    [
        (Item, "potion", {"cost": 5}, 2, False, 40),  # buy item
        (Item, "potion", {"cost": 5}, 1, True, 5),  # sell item
        (
            Monster,
            "rockitten",
            {"name": "rockitten", "hp": 100},
            1,
            False,
            100,
        ),  # buy monster
        (
            Monster,
            "rockitten",
            {"name": "rockitten", "hp": 100},
            1,
            True,
            50,
        ),  # sell monster
        (
            Monster,
            "unknown_monster",
            {"name": "unknown_monster", "hp": 20},
            1,
            True,
            round(20 * 0.5),
        ),  # monster w/o model
    ],
)
def test_calculate_price(
    economy, entity_cls, slug, kwargs, quantity, seller_mode, expected_price
):
    mock_entity = MagicMock(spec=entity_cls)
    mock_entity.slug = slug
    for k, v in kwargs.items():
        setattr(mock_entity, k, v)

    price, discount = economy.calculate_price(
        mock_entity, quantity=quantity, seller_mode=seller_mode
    )
    assert price == expected_price
    assert discount == 0
