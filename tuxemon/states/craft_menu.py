# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.constants import paths
from tuxemon.item.crafting_system import CraftingSystem
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.item.recipe import Recipe


class CraftMenuState(PygameMenuState):
    """
    This state is responsible for the craft menu.
    """

    name: ClassVar[str] = "CraftMenuState"

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        file_yaml: str,
        method: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.character = character
        self.file_yaml = file_yaml
        self.method = method
        self.crafting_system = CraftingSystem()
        self.crafting_system.set_current_method(self.method)

        width, height = client.context.resolution

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        self._menu_config["theme"] = theme

        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:

        def up() -> None:
            menu._scrollarea._scrollbars[0].bump_to_top()

        yaml_path = (paths.mods_folder / self.file_yaml).resolve()
        if not yaml_path.exists():
            raise FileNotFoundError(f"Recipe file not found: {yaml_path}")

        self.crafting_system.load_recipes(yaml_path)

        craftable_recipes = []

        for slug, recipe in self.crafting_system.recipes.items():
            if self.crafting_system.check_can_craft(slug, self.character.bag):
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

    def add_craft_button(self, menu: Menu, slug: str, recipe: Recipe) -> None:

        def craft(recipe_slug: str) -> None:
            self.client.remove_state_by_name("CraftMenuState")
            result = self.crafting_system.craft_item_for_bag(
                recipe_slug, self.character.bag
            )
            if result.revealed_content_slug:
                open_dialog(
                    self.client,
                    [T.translate(result.revealed_content_slug)],
                    dialog_speed="max",
                )
            else:
                open_dialog(
                    self.client,
                    [T.translate(result.message_slug)],
                    dialog_speed="max",
                )

        menu.add.button(title=T.translate(slug), action=partial(craft, slug))
        if recipe.recipe_text:
            menu.add.label(
                title=T.translate(recipe.recipe_text),
                font_size=self.font_type.small,
                wordwrap=True,
            )

    def add_tool_label(self, menu: Menu, recipe: Recipe) -> None:
        for tool in recipe.required_tools:
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

    def add_ingredient_label(self, menu: Menu, recipe: Recipe) -> None:
        items = f"{T.translate('menu_items')}: {T.translate(recipe.get_ingredients_str())}"
        menu.add.label(
            title=items,
            font_size=self.font_type.small,
            wordwrap=True,
        )
