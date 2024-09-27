# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator, Sequence

import pygame

from tuxemon import prepare, tools
from tuxemon.db import State
from tuxemon.item.item import Item
from tuxemon.item.itemeffect import ItemEffectResult
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.states.monster import MonsterMenuState
from tuxemon.ui.text import TextArea


def sort_inventory(
    inventory: Sequence[Item],
) -> Sequence[Item]:
    """
    Sort inventory in a usable way. Expects an iterable of inventory properties.

    * Group items by category
    * Sort in groups by name
    * Group order: Potions, Food, Utility Items, Quest/Game Items

    Parameters:
        inventory: NPC inventory values.

    Returns:
        Sorted copy of the inventory.

    """

    def rank_item(item: Item) -> tuple[int, str]:
        primary_order = sort_order.index(item.sort)
        return primary_order, item.name

    # the two reversals are used to let name sort desc, but class sort asc
    sort_order = ["potion", "food", "utility", "quest"]
    sort_order.reverse()
    return sorted(inventory, key=rank_item, reverse=True)


class ItemMenuState(Menu[Item]):
    """The item menu allows you to view and use items in your inventory."""

    background_filename = prepare.BG_ITEMS
    draw_borders = False

    def __init__(self) -> None:
        super().__init__()

        # this sprite is used to display the item
        # it's also animated to pop out of the backpack
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.load_sprite(
            prepare.BG_ITEMS_BACKPACK,
            center=self.backpack_center,
            layer=100,
        )

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def determine_state_called_from(self) -> str:
        dex = self.client.active_states.index(self)
        return self.client.active_states[dex + 1].name

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        """
        Called when player has selected something from the inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.
        """
        item = menu_item.game_object

        # Check if the item can be used on any monster
        if not any(item.validate(m) for m in local_session.player.monsters):
            self.on_menu_selection_change()
            error_message = self.get_error_message(item)
            tools.open_dialog(local_session, [error_message])
        # Check if the item can be used in the current state
        elif not any(
            s.name in self.client.active_state_names for s in item.usable_in
        ):
            error_message = T.format(
                "item_cannot_use_here", {"name": item.name}
            )
            tools.open_dialog(local_session, [error_message])
        else:
            self.open_confirm_use_menu(item)

    def get_error_message(self, item: Item) -> str:
        """
        Returns an error message based on the item's conditions.

        Parameters:
            item: The item to check.

        Returns:
            An error message.
        """
        for condition in item.conditions:
            if condition.name == "location_inside":
                loc_inside = getattr(condition, "location_inside")
                return T.format(
                    "item_used_wrong_location_inside",
                    {
                        "name": item.name.upper(),
                        "here": T.translate(loc_inside),
                    },
                )
            elif condition.name == "location_type":
                loc_type = getattr(condition, "location_type")
                return T.format(
                    "item_used_wrong_location_type",
                    {
                        "name": item.name.upper(),
                        "here": T.translate(loc_type),
                    },
                )
            elif condition.name in ["facing_tile", "facing_sprite"]:
                return T.format("item_cannot_use_here", {"name": item.name})
        return T.format("item_no_available_target", {"name": item.name})

    def open_confirm_use_menu(self, item: Item) -> None:
        """
        Confirm if player wants to use this item, or not.

        Parameters:
            item: Selected item.
        """

        def show_item_result(item: Item, result: ItemEffectResult) -> None:
            """Show the item result as a dialog if necessary."""
            if (
                item.behaviors.show_dialog_on_failure and not result["success"]
            ) or (item.behaviors.show_dialog_on_success and result["success"]):
                tools.show_item_result_as_dialog(local_session, item, result)

        def use_item_with_monster(menu_item: MenuItem[Monster]) -> None:
            """Use the item with a monster."""
            player = local_session.player
            monster = menu_item.game_object
            result = item.use(player, monster)
            self.client.remove_state_by_name("MonsterMenuState")
            self.client.remove_state_by_name("ItemMenuState")
            self.client.remove_state_by_name("WorldMenuState")
            show_item_result(item, result)

        def use_item_without_monster() -> None:
            """Use the item without a monster."""
            player = local_session.player
            self.client.remove_state_by_name("ItemMenuState")
            self.client.remove_state_by_name("WorldMenuState")
            result = item.use(player, None)
            show_item_result(item, result)

        def confirm() -> None:
            """Confirm the use of the item."""
            self.client.remove_state_by_name("ChoiceState")
            if item.behaviors.requires_monster_menu:
                menu = self.client.push_state(MonsterMenuState())
                menu.is_valid_entry = item.validate  # type: ignore[assignment]
                menu.on_menu_selection = use_item_with_monster  # type: ignore[assignment]
            else:
                use_item_without_monster()

        def cancel() -> None:
            """Cancel the use of the item."""
            self.client.remove_state_by_name("ChoiceState")

        def open_choice_menu() -> None:
            """Open the use/cancel menu."""
            menu_options = [
                ("use", T.translate("item_confirm_use").upper(), confirm),
                ("cancel", T.translate("item_confirm_cancel").upper(), cancel),
            ]
            tools.open_choice_dialog(local_session, menu_options, True)

        open_choice_menu()

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        state = self.determine_state_called_from()
        inventory = self.get_inventory(state)

        if not inventory:
            return

        for obj in sort_inventory(inventory):
            label = f"{obj.name} x {obj.quantity}"
            image = self.shadow_text(label, bg=prepare.DIMGRAY_COLOR)
            yield MenuItem(image, obj.name, obj.description, obj)

    def get_inventory(self, state: str) -> list[Item]:
        """Get player inventory items based on the current state."""
        if state == "MainCombatMenuState":
            return [
                item
                for item in local_session.player.items
                if State[state] in item.usable_in
            ]
        else:
            return [
                item
                for item in local_session.player.items
                if item.behaviors.visible
            ]

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        selected_item = self.get_selected_item()
        if selected_item:
            self.animate_item_selection(selected_item.game_object)
            self.show_item_description(selected_item.game_object)

    def animate_item_selection(self, item: Item) -> None:
        """Animate the selected item being pulled from the bag."""
        image = item.surface
        assert image
        self.item_sprite.image = image
        self.item_sprite.rect = image.get_rect(center=self.backpack_center)
        self.animate(
            self.item_sprite.rect,
            centery=self.item_center[1],
            duration=0.2,
        )

    def show_item_description(self, item: Item) -> None:
        """Show the description of the selected item."""
        if item.description:
            self.alert(item.description)
