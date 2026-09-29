# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import EconomyItemModel, EconomyModel, EconomyMonsterModel
from tuxemon.economy.economy import Economy
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster


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


@pytest.mark.parametrize(
    "slug,expected_level,expected_inventory",
    [
        pytest.param("rockitten", 5, 1, id="rockitten"),
        pytest.param("pairagrin", 1, 50, id="pairagrin"),
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
    "entity_cls,slug,kwargs,quantity,seller_mode,expected_price",
    [
        pytest.param(
            Item,
            "potion",
            {"cost": 5},
            2,
            False,
            40,
            id="buy_item",
        ),
        pytest.param(
            Item,
            "potion",
            {"cost": 5},
            1,
            True,
            5,
            id="sell_item",
        ),
        pytest.param(
            Monster,
            "rockitten",
            {"name": "rockitten", "hp": 100},
            1,
            False,
            100,
            id="buy_monster",
        ),
        pytest.param(
            Monster,
            "rockitten",
            {"name": "rockitten", "hp": 100},
            1,
            True,
            50,
            id="sell_monster",
        ),
        pytest.param(
            Monster,
            "unknown_monster",
            {"name": "unknown_monster", "hp": 20},
            1,
            True,
            round(20 * 0.5),
            id="monster_without_model",
        ),
    ],
)
def test_calculate_price(
    economy, entity_cls, slug, kwargs, quantity, seller_mode, expected_price
):
    mock_entity = MagicMock(spec=entity_cls)
    mock_entity.slug = slug
    for k, v in kwargs.items():
        setattr(mock_entity, k, v)

    price = economy.calculate_price(
        mock_entity, quantity=quantity, seller_mode=seller_mode
    )
    assert price.final_price == expected_price
    assert price.modifier_percent == 0


def test_get_model_for_item(economy):
    mock_item = MagicMock(spec=Item)
    mock_item.slug = "potion"
    model = economy.get_model_for(mock_item)
    assert isinstance(model, EconomyItemModel)
    assert model.slug == "potion"


def test_get_model_for_monster(economy):
    mock_monster = MagicMock(spec=Monster)
    mock_monster.slug = "rockitten"
    model = economy.get_model_for(mock_monster)
    assert isinstance(model, EconomyMonsterModel)
    assert model.slug == "rockitten"


def test_get_model_for_unknown(economy):
    mock_item = MagicMock(spec=Item)
    mock_item.slug = "does_not_exist"
    assert economy.get_model_for(mock_item) is None


def test_calculate_price_missing_monster_price_raises(economy):
    mock_monster = MagicMock(spec=Monster)
    mock_monster.slug = "ghost"
    mock_monster.hp = 10
    with pytest.raises(ValueError):
        economy.calculate_price(mock_monster, quantity=1, seller_mode=False)


def test_calculate_price_missing_item_cost_resale(economy):
    mock_item = MagicMock(spec=Item)
    mock_item.slug = "revive"  # cost=0 in model
    mock_item.cost = 0
    price = economy.calculate_price(mock_item, quantity=1, seller_mode=True)
    assert price.final_price == 0
    assert price.modifier_percent == 0


def test_calculate_price_item_without_model_resale(economy):
    mock_item = MagicMock(spec=Item)
    mock_item.slug = "unknown_item"
    mock_item.cost = 12
    price = economy.calculate_price(mock_item, quantity=1, seller_mode=True)
    assert price.final_price == round(12 * economy.model.resale_multiplier)
    assert price.modifier_percent == 0


def test_calculate_price_item_without_model_purchase(economy):
    mock_item = MagicMock(spec=Item)
    mock_item.slug = "unknown_item"
    mock_item.cost = 20
    price = economy.calculate_price(mock_item, quantity=1, seller_mode=False)
    assert price.final_price == round(20 * economy.model.resale_multiplier)
    assert price.modifier_percent == 0
