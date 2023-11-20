# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator, Sequence

import pygame

from tuxemon import tools
from tuxemon.db import State
from tuxemon.item.item import Item
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

    background_filename = "gfx/ui/item/item_menu_bg.png"
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
            "gfx/ui/item/backpack.png",
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
        active_state_names = [a.name for a in self.client.active_states]

        if not any(item.validate(m) for m in local_session.player.monsters):
            self.on_menu_selection_change()
            msg = T.format("item_no_available_target", {"name": item.name})
            for i in item.conditions:
                if i.name == "location_inside":
                    loc_inside = getattr(i, "location_inside")
                    msg = T.format(
                        "item_used_wrong_location_inside",
                        {
                            "name": item.name,
                            "here": T.translate(loc_inside),
                        },
                    )
                elif i.name == "location_type":
                    loc_type = getattr(i, "location_type")
                    msg = T.format(
                        "item_used_wrong_location_type",
                        {
                            "name": item.name,
                            "here": T.translate(loc_type),
                        },
                    )
                elif i.name == "facing_tile" or i.name == "facing_sprite":
                    msg = T.format("item_cannot_use_here", {"name": item.name})
            tools.open_dialog(local_session, [msg])
        elif not any(s.name in active_state_names for s in item.usable_in):
            msg = T.format("item_cannot_use_here", {"name": item.name})
            tools.open_dialog(local_session, [msg])
        else:
            self.open_confirm_use_menu(item)

    def open_confirm_use_menu(self, item: Item) -> None:
        """
        Confirm if player wants to use this item, or not.

        Parameters:
            item: Selected item.

        """

        def use_item(menu_item: MenuItem[Monster]) -> None:
            player = local_session.player
            monster = menu_item.game_object

            # item must be used before state is popped.
            result = item.use(player, monster)
            self.client.pop_state()  # pop the monster screen
            self.client.pop_state()  # pop the item screen
            # check effects, some don't need the show_item_result_as_dialog
            # (e.g. learn_mm, etc)
            for t in item.effects:
                if t.name == "learn_mm" or t.name == "learn_tm":
                    if result["success"]:
                        player.check_max_moves(local_session, monster)
                    else:
                        tools.show_item_result_as_dialog(
                            local_session, item, result
                        )
                else:
                    tools.show_item_result_as_dialog(
                        local_session, item, result
                    )

        def use_item_no_monster(itm: Item) -> None:
            player = local_session.player
            self.client.pop_state()
            result = itm.use(player, None)
            if item.category == "fish" and not result["success"]:
                tools.show_item_result_as_dialog(local_session, item, result)
            elif item.category == "fish" and result["success"]:
                pass
            else:
                tools.show_item_result_as_dialog(local_session, item, result)

        def confirm() -> None:
            self.client.pop_state()  # close the confirm dialog
            categories = ["fish", "destroy"]  # not opening monster menu

            if item.category in categories:
                use_item_no_monster(item)
            else:
                menu = self.client.push_state(MonsterMenuState())
                menu.is_valid_entry = item.validate  # type: ignore[assignment]
                menu.on_menu_selection = use_item  # type: ignore[assignment]

        def cancel() -> None:
            self.client.pop_state()  # close the use/cancel menu

        def open_choice_menu() -> None:
            # open the menu for use/cancel
            tools.open_choice_dialog(
                local_session,
                menu=(
                    (
                        "use",
                        T.translate("item_confirm_use").upper(),
                        confirm,
                    ),
                    (
                        "cancel",
                        T.translate("item_confirm_cancel").upper(),
                        cancel,
                    ),
                ),
                escape_key_exits=True,
            )

        open_choice_menu()

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        state = self.determine_state_called_from()
        inventory = []
        # in battle shows only items with MainCombatMenuState (usable_in)
        if state == "MainCombatMenuState":
            inventory = [
                item
                for item in local_session.player.items
                if State[state] in item.usable_in
            ]
        # shows all items (only visible)
        else:
            inventory = [
                item for item in local_session.player.items if item.visible
            ]

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        for obj in sort_inventory(inventory):
            label = obj.name + " x " + str(obj.quantity)
            image = self.shadow_text(label, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        item = self.get_selected_item()
        if item:
            # animate item being pulled from the bag
            image = item.game_object.surface
            assert image
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.backpack_center)
            self.animate(
                self.item_sprite.rect,
                centery=self.item_center[1],
                duration=0.2,
            )

            # show item description
            if item.description:
                self.alert(item.description)
