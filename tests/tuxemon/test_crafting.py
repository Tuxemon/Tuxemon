# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.item.crafting_system import CraftingSystem
from tuxemon.item.item import Item
from tuxemon.item.recipe import Recipe


@pytest.fixture
def system():
    return CraftingSystem()


@pytest.fixture
def recipe_slug():
    return "healing_potion"


@pytest.fixture
def recipe(recipe_slug):
    return Recipe(
        {
            "recipe_slug": recipe_slug,
            "required_ingredients": {"herb": 2, "water": 1},
            "required_tools": [{"slug": "mortar", "consumed": True}],
            "possible_outputs": [
                {"slug": "potion", "type": "item", "quantity": 1, "weight": 1}
            ],
            "crafting_method": None,
        }
    )


@pytest.fixture
def bag():
    bag = MagicMock()
    bag.get_all_item_quantities.return_value = {
        "herb": 2,
        "water": 1,
        "mortar": 1,
    }
    bag.has_item.side_effect = lambda slug: slug in ["herb", "water", "mortar"]
    bag.find_item.side_effect = lambda slug: MagicMock(quantity=2, slug=slug)
    return bag


@pytest.fixture
def mock_item_create():
    """Patch Item.create so crafting returns a predictable mock item."""
    item_mock = MagicMock(spec=Item)
    item_mock.slug = "potion"
    item_mock.quantity = 1

    with patch("tuxemon.item.item.Item.create", return_value=item_mock):
        yield item_mock


@pytest.fixture
def setup_recipe(system, recipe_slug, recipe):
    system.recipes[recipe_slug] = recipe
    return system


def test_successful_craft(setup_recipe, bag, mock_item_create, recipe_slug):
    result = setup_recipe.craft_item_for_bag(recipe_slug, bag)

    assert result.success
    assert result.message_slug == "generic_success"
    assert result.output_type == "item"
    assert len(result.crafted_items) == 1
    assert result.crafted_items[0].slug == "potion"


def test_missing_recipe(system, bag):
    result = system.craft_item_for_bag("unknown_slug", bag)

    assert not result.success
    assert result.message_slug == "invalid_recipe"


def test_check_can_craft_blocks_execution(setup_recipe, bag):
    setup_recipe.check_can_craft = MagicMock(return_value=False)

    result = setup_recipe.craft_item_for_bag("healing_potion", bag)

    assert not result.success
    assert result.failure_reason == "Missing required ingredients."


def test_tool_consumption(setup_recipe, bag, mock_item_create):
    tool = MagicMock(quantity=1)
    bag.find_item.side_effect = lambda slug: (
        tool if slug == "mortar" else MagicMock(quantity=2)
    )

    result = setup_recipe.craft_item_for_bag("healing_potion", bag)

    bag.remove_item.assert_called_with(tool)
    assert result.success


def test_output_type_lore_trigger(setup_recipe, bag):
    setup_recipe.recipes["healing_potion"].possible_outputs = [
        {"slug": "ancient_scroll", "type": "lore_trigger", "weight": 1}
    ]

    result = setup_recipe.craft_item_for_bag("healing_potion", bag)

    assert result.success
    assert result.output_type == "lore_trigger"
    assert result.message_slug == "lore_trigger_success"
    assert result.revealed_content_slug == "ancient_scroll"


def test_output_type_quest_trigger(setup_recipe, bag):
    setup_recipe.recipes["healing_potion"].possible_outputs = [
        {"slug": "quest_start", "type": "quest_trigger", "weight": 1}
    ]

    result = setup_recipe.craft_item_for_bag("healing_potion", bag)

    assert result.success
    assert result.output_type == "quest_trigger"
    assert result.message_slug == "quest_trigger_success"
    assert result.revealed_content_slug == "quest_start"


def test_unknown_output_type_raises(setup_recipe, bag):
    setup_recipe.recipes["healing_potion"].possible_outputs = [
        {"slug": "mystery", "type": "unknown", "weight": 1}
    ]

    with pytest.raises(ValueError):
        setup_recipe.craft_item_for_bag("healing_potion", bag)
