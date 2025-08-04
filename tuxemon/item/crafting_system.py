# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.item.item import Item
from tuxemon.item.recipe import Recipe

if TYPE_CHECKING:
    from tuxemon.npc import NPCBagHandler

logger = logging.getLogger(__name__)


@dataclass
class CraftingResult:
    success: bool
    message_slug: str
    output_type: str
    crafted_items: list[Item] = field(default_factory=list)
    failure_reason: Optional[str] = None
    used_method: Optional[str] = None
    revealed_content_slug: Optional[str] = None


class CraftingSystem:
    """
    Manages crafting operations using recipe rules and live NPCBagHandler contents.
    No static item definitions required.
    """

    def __init__(self) -> None:
        self.recipes: dict[str, Recipe] = {}
        self._current_method_slug: Optional[str] = None

    def set_current_method(self, method_slug: Optional[str]) -> None:
        """Sets the current crafting method the player is using."""
        self._current_method_slug = method_slug
        logger.debug(f"Current crafting method set to: {method_slug}")

    def load_recipes(self, filepath: Path) -> None:
        """Loads crafting recipes from a YAML file."""
        loaded_recipes = Recipe.load_from_yaml(filepath)
        for recipe in loaded_recipes:
            if hasattr(recipe, "recipe_slug"):
                self.recipes[recipe.recipe_slug] = recipe
            else:
                logger.warning("Skipping recipe without 'recipe_slug'.")

    def select_weighted_output(
        self, possible_outputs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Selects one of the possible outputs based on defined weights.
        """
        total_weight = sum(entry["weight"] for entry in possible_outputs)
        roll = random.uniform(0, total_weight)

        cumulative = 0
        for entry in possible_outputs:
            cumulative += entry["weight"]
            if roll <= cumulative:
                return entry

        return possible_outputs[-1]

    def check_can_craft(
        self, recipe_slug: str, npc_bag_handler: NPCBagHandler
    ) -> bool:
        """
        Determines if a recipe can be crafted, based on the player's inventory
        and tool availability.
        """
        recipe = self.recipes.get(recipe_slug)
        if not recipe:
            logger.debug(f"[Craft] Recipe '{recipe_slug}' not found.")
            return False

        # Check required crafting method (if specified)
        if recipe.crafting_method:
            if self._current_method_slug is None:
                logger.debug(
                    f"[Craft] Recipe '{recipe_slug}' requires a method ('{recipe.crafting_method}'), but no current method is set."
                )
                return False
            if recipe.crafting_method != self._current_method_slug:
                logger.debug(
                    f"[Craft] Recipe '{recipe_slug}' requires method '{recipe.crafting_method}', "
                    f"but current method is '{self._current_method_slug}'."
                )
                return False

        # Check required tool (if specified)
        for tool_entry in recipe.required_tools:
            tool_slug = tool_entry.get("slug")
            if not tool_slug:
                logger.debug("[Craft] Tool entry missing 'slug'. Skipping.")
                continue
            if not npc_bag_handler.has_item(tool_slug):
                logger.debug(f"[Craft] Missing required tool: '{tool_slug}'.")
                return False

        # Check required ingredients
        item_quantities = npc_bag_handler.get_all_item_quantities()
        for slug, required_qty in recipe.required_ingredients.items():
            current_qty = item_quantities.get(slug, 0)
            if current_qty < required_qty:
                logger.debug(
                    f"[Craft] Not enough '{slug}'. Needed: {required_qty}, available: {current_qty}."
                )
                return False

        logger.debug(
            f"[Craft] All requirements met for recipe '{recipe_slug}'."
        )
        return True

    def craft_item_for_bag(
        self, recipe_slug: str, npc_bag_handler: NPCBagHandler
    ) -> CraftingResult:
        logger.debug(f"[Craft] Attempting to craft recipe: '{recipe_slug}'")

        if not self.check_can_craft(recipe_slug, npc_bag_handler):
            logger.debug(
                f"[Craft] Preconditions not met for recipe '{recipe_slug}'."
            )
            return CraftingResult(
                success=False,
                message_slug="generic_failure",
                output_type="",
                crafted_items=[],
                failure_reason="Missing required ingredients.",
            )

        recipe = self.recipes.get(recipe_slug)
        if not recipe:
            logger.debug(
                f"[Craft] Recipe slug '{recipe_slug}' not found in database."
            )
            return CraftingResult(
                success=False,
                message_slug="invalid_recipe",
                output_type="",
                crafted_items=[],
                failure_reason=f"Recipe '{recipe_slug}' not found.",
            )

        for item_slug, item_quantity in recipe.required_ingredients.items():
            item = npc_bag_handler.find_item(item_slug)
            if not item or item.quantity < item_quantity:
                logger.debug(
                    f"[Craft] Missing or insufficient '{item_slug}' (needed: {item_quantity}, available: {item.quantity if item else 0})"
                )
                return CraftingResult(
                    success=False,
                    message_slug="generic_failure",
                    output_type="",
                    crafted_items=[],
                    failure_reason=f"Missing or insufficient '{item_slug}'",
                )

            if item.quantity > item_quantity:
                item.decrease_quantity(item_quantity)
                logger.debug(
                    f"[Craft] Decreased '{item_slug}' by {item_quantity}"
                )
            else:
                npc_bag_handler.remove_item(item)
                logger.debug(
                    f"[Craft] Removed '{item_slug}' (exact quantity matched)"
                )

        crafted_items: list[Item] = []
        revealed_content_slug: Optional[str] = None
        message_slug: str = "generic_success"

        selected = self.select_weighted_output(recipe.possible_outputs)
        slug: str = selected["slug"]
        output_type: str = selected.get("type", "item")
        qty: int = selected.get("quantity", 1)
        logger.debug(
            f"[Craft] Selected output: {slug} x{qty} (type: {output_type})"
        )

        if output_type == "item":
            if npc_bag_handler.has_item(slug):
                existing = npc_bag_handler.find_item(slug)
                if existing:
                    existing.set_quantity(existing.quantity + qty)
                    crafted_items.append(existing)
                    logger.debug(
                        f"[Craft] Increased quantity of existing item '{slug}' by {qty}"
                    )
            else:
                new_item = Item().create(slug)
                npc_bag_handler.add_item(new_item, qty)
                crafted_items.append(new_item)
                logger.debug(f"[Craft] Added new item '{slug}' x{qty} to bag")
        elif output_type == "lore_trigger":
            revealed_content_slug = slug
            message_slug = "lore_trigger_success"
            logger.debug(f"[Craft] Lore trigger activated for slug '{slug}'")
        elif output_type == "quest_trigger":
            revealed_content_slug = slug
            message_slug = "quest_trigger_success"
            logger.debug(f"[Craft] Quest trigger activated for slug '{slug}'")
        else:
            raise ValueError(
                f"[Craft] Unknown output type '{output_type}' for slug '{slug}'"
            )

        # Consume tools if necessary
        for tool_entry in recipe.required_tools:
            tool_slug = tool_entry.get("slug")
            consumed = tool_entry.get("consumed", False)

            if not tool_slug:
                logger.debug(
                    "[Craft] Tool marked for consumption is missing a 'slug'. Skipping."
                )
                continue

            if consumed:
                tool = npc_bag_handler.find_item(tool_slug)
                if tool:
                    if tool.quantity > 1:
                        tool.decrease_quantity()
                        logger.debug(
                            f"[Craft] Consumed one unit of tool '{tool_slug}'"
                        )
                    else:
                        npc_bag_handler.remove_item(tool)
                        logger.debug(
                            f"[Craft] Removed tool '{tool_slug}' from bag (last unit)"
                        )

        logger.debug(
            f"[Craft] Crafting of '{recipe_slug}' completed successfully."
        )

        return CraftingResult(
            success=True,
            message_slug=message_slug,
            output_type=output_type,
            crafted_items=crafted_items,
            revealed_content_slug=revealed_content_slug,
        )
