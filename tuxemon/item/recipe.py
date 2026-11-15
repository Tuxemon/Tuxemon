# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T

logger = logging.getLogger(__name__)


class Recipe:
    """
    Represents a crafting recipe.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.recipe_slug: str = data["recipe_slug"]
        self.recipe_text: str | None = data.get("recipe_text", None)
        self.possible_outputs: list[dict[str, Any]] = data.get(
            "possible_outputs", []
        )
        self.required_ingredients: dict[str, int] = data.get(
            "required_ingredients", {}
        )
        self.crafting_method: str | None = data.get("crafting_method", None)
        self.required_tools: list[dict[str, Any]] = data.get(
            "required_tools", []
        )

    def get_ingredients_str(self) -> str:
        """
        Returns a simple string listing all ingredients and their quantities,
        like: '2x wood, 1x stone, 3x rope'
        """
        return ", ".join(
            f"{qty}x {T.translate(slug)}"
            for slug, qty in self.required_ingredients.items()
        )

    @staticmethod
    def load_from_yaml(filepath: Path) -> list[Recipe]:
        """
        Loads a list of Recipe objects from a YAML file.
        """
        recipes: list[Recipe] = []

        try:
            data = load_yaml(filepath)

            if isinstance(data, list):
                for recipe_data in data:
                    if isinstance(recipe_data, dict):
                        recipes.append(Recipe(recipe_data))
                    else:
                        logger.debug(
                            f"Warning: Skipping non-dictionary item in YAML: {recipe_data}"
                        )
            else:
                logger.debug(
                    f"Error: YAML file does not contain a list of recipes. "
                    f"Found type: {type(data)}"
                )

        except Exception as e:
            logger.debug(f"Failed to load recipes from '{filepath}': {e}")

        return recipes
