# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.constants import paths
from tuxemon.item.crafting_system import CraftingSystem
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.item.recipe import Recipe
    from tuxemon.npc import NPC


class CraftMenuState(PygameMenuState):
    """
    This state is responsible for the craft menu.
    """

    def __init__(self, character: NPC, method: Optional[str] = None) -> None:
        self.character = character
        self.method = method
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MISSIONS)
        theme.scrollarea_position = locals.POSITION_EAST

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.crafting_system = CraftingSystem()
        self.crafting_system.set_current_method(self.method)
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: pygame_menu.Menu) -> None:

        def up() -> None:
            menu._scrollarea._scrollbars[0].bump_to_top()

        yaml_path = (paths.mods_folder / "recipes.yaml").resolve()
        if not yaml_path.exists():
            raise FileNotFoundError(f"Recipe file not found: {yaml_path}")

        self.crafting_system.load_recipes(yaml_path)

        craftable_recipes = []

        for slug, recipe in self.crafting_system.recipes.items():
            if self.crafting_system.check_can_craft(
                slug, self.character.items
            ):
                craftable_recipes.append((slug, recipe))

        if not craftable_recipes:
            menu.add.label(
                title=T.translate("menu_no_craftable_items"),
            )
        else:
            for slug, recipe in craftable_recipes:
                self.add_craft_button(menu, slug, recipe)
                self.add_tool_label(menu, recipe)
                self.add_ingredient_label(menu, recipe)
            menu.add.button(T.translate("menu_to_the_top"), action=up)

    def add_craft_button(
        self, menu: pygame_menu.Menu, slug: str, recipe: Recipe
    ) -> None:

        def craft(recipe_slug: str) -> None:
            self.client.remove_state_by_name("CraftMenuState")
            result = self.crafting_system.craft_item_for_bag(
                recipe_slug, self.character.items
            )
            if result.revealed_content_slug:
                open_dialog(
                    self.client,
                    [T.translate(result.revealed_content_slug)],
                )
            else:
                open_dialog(self.client, [T.translate(result.message_slug)])

        menu.add.button(title=T.translate(slug), action=partial(craft, slug))
        if recipe.recipe_text:
            menu.add.label(
                title=T.translate(recipe.recipe_text),
                font_size=self.font_type.small,
                wordwrap=True,
            )

    def add_tool_label(self, menu: pygame_menu.Menu, recipe: Recipe) -> None:
        for tool in getattr(recipe, "required_tools", []):
            tool_name = T.translate(tool.get("slug", ""))
            consumed_text = (
                T.translate("menu_tool_consumed")
                if tool.get("consumed", False)
                else T.translate("menu_tool_not_consumed")
            )
            tool_text = f"{T.translate('menu_craft_tools')}: {tool_name} ({consumed_text})"
            menu.add.label(
                title=tool_text,
                font_size=self.font_type.small,
                wordwrap=True,
            )

    def add_ingredient_label(
        self, menu: pygame_menu.Menu, recipe: Recipe
    ) -> None:
        items = f"{T.translate('menu_items')}: {T.translate(recipe.get_ingredients_str())}"
        menu.add.label(
            title=items,
            font_size=self.font_type.small,
            wordwrap=True,
        )
