# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.item.crafting_system import CraftingSystem
from tuxemon.item.item import Item
from tuxemon.item.recipe import Recipe


class TestCraftingSystem(unittest.TestCase):
    def setUp(self):
        self.system = CraftingSystem()

        # Create a mock recipe
        self.recipe_slug = "healing_potion"
        self.recipe = Recipe(
            {
                "recipe_slug": self.recipe_slug,
                "required_ingredients": {"herb": 2, "water": 1},
                "required_tools": [{"slug": "mortar", "consumed": True}],
                "possible_outputs": [
                    {
                        "slug": "potion",
                        "type": "item",
                        "quantity": 1,
                        "weight": 1,
                    }
                ],
                "crafting_method": None,
            }
        )
        self.system.recipes[self.recipe_slug] = self.recipe

        # Mock BagHandler
        self.bag = MagicMock()
        self.bag.get_all_item_quantities.return_value = {
            "herb": 2,
            "water": 1,
            "mortar": 1,
        }
        self.bag.has_item.side_effect = lambda slug: slug in [
            "herb",
            "water",
            "mortar",
        ]
        self.bag.find_item.side_effect = lambda slug: MagicMock(
            quantity=2, slug=slug
        )

        # Patch Item creation
        self.item_mock = MagicMock(spec=Item)
        self.item_mock.slug = "potion"
        self.item_mock.quantity = 1
        self.item_mock.create.return_value = self.item_mock

        patcher = patch(
            "tuxemon.item.item.Item.create", return_value=self.item_mock
        )
        self.addCleanup(patcher.stop)
        self.mock_create = patcher.start()

    def test_successful_craft(self):
        result = self.system.craft_item_for_bag(self.recipe_slug, self.bag)
        self.assertTrue(result.success)
        self.assertEqual(result.message_slug, "generic_success")
        self.assertEqual(result.output_type, "item")
        self.assertEqual(len(result.crafted_items), 1)
        self.assertEqual(result.crafted_items[0].slug, "potion")

    def test_missing_recipe(self):
        result = self.system.craft_item_for_bag("unknown_slug", self.bag)
        self.assertFalse(result.success)
        self.assertEqual(result.message_slug, "invalid_recipe")

    def test_check_can_craft_blocks_execution(self):
        # Simulate missing ingredients
        self.system.check_can_craft = MagicMock(return_value=False)
        result = self.system.craft_item_for_bag(self.recipe_slug, self.bag)
        self.assertFalse(result.success)
        self.assertEqual(
            result.failure_reason, "Missing required ingredients."
        )

    def test_tool_consumption(self):
        tool = MagicMock(quantity=1)
        self.bag.find_item.side_effect = lambda slug: (
            tool if slug == "mortar" else MagicMock(quantity=2)
        )
        result = self.system.craft_item_for_bag(self.recipe_slug, self.bag)
        self.bag.remove_item.assert_called_with(tool)
        self.assertTrue(result.success)

    def test_output_type_lore_trigger(self):
        self.recipe.possible_outputs = [
            {"slug": "ancient_scroll", "type": "lore_trigger", "weight": 1}
        ]
        result = self.system.craft_item_for_bag(self.recipe_slug, self.bag)
        self.assertTrue(result.success)
        self.assertEqual(result.output_type, "lore_trigger")
        self.assertEqual(result.message_slug, "lore_trigger_success")
        self.assertEqual(result.revealed_content_slug, "ancient_scroll")

    def test_output_type_quest_trigger(self):
        self.recipe.possible_outputs = [
            {"slug": "quest_start", "type": "quest_trigger", "weight": 1}
        ]
        result = self.system.craft_item_for_bag(self.recipe_slug, self.bag)
        self.assertTrue(result.success)
        self.assertEqual(result.output_type, "quest_trigger")
        self.assertEqual(result.message_slug, "quest_trigger_success")
        self.assertEqual(result.revealed_content_slug, "quest_start")

    def test_unknown_output_type_raises(self):
        self.recipe.possible_outputs = [
            {"slug": "mystery", "type": "unknown", "weight": 1}
        ]
        with self.assertRaises(ValueError):
            self.system.craft_item_for_bag(self.recipe_slug, self.bag)
