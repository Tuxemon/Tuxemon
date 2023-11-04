# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Optional

from tuxemon.db import ItemCategory
from tuxemon.graphics import ColorLike
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.monster import Monster
from tuxemon.states.items import ItemMenuState

if TYPE_CHECKING:
    from tuxemon.states.park.park import ParkState


MenuGameObj = Callable[[], None]


class MainParkMenuState(PopUpMenu[MenuGameObj]):
    """
    Main menu: Ball, Item, Swap, Run

    """

    unavailable_color: ColorLike = (220, 220, 220)
    escape_key_exits = False
    columns = 2

    def __init__(self, cmb: ParkState, monster: Monster) -> None:
        super().__init__()
        self.combat = cmb
        self.player = cmb.players[0]  # human
        self.enemy = cmb.players[1]  # ai
        self.monster = monster
        self.opponents = cmb.monsters_in_play[self.enemy]
        self.description: Optional[str] = None

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        menu_items_map = (
            ("menu_ball", self.throw_tuxeball),
            ("menu_food", self.open_item_menu),
            ("menu_doll", self.open_item_menu),
            ("menu_run", self.run),
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            itm = 1
            if key == "menu_ball":
                itm = self.check_item("tuxeball_park")
                if itm > 0:
                    label = f"{label}x{itm}"
            if key == "menu_food":
                itm = self.check_category("food")
                if itm > 0:
                    label = f"{label}x{itm}"
            if key == "menu_doll":
                itm = self.check_category("doll")
                if itm > 0:
                    label = f"{label}x{itm}"
            image = (
                self.shadow_text(label)
                if itm > 0
                else self.shadow_text(label, fg=self.unavailable_color)
            )
            menu = MenuItem(image, label, key, callback)
            if itm == 0:
                menu.enabled = False
            yield menu

    def run(self) -> None:
        for remove in self.combat.players:
            self.combat.clean_combat()
            del self.combat.monsters_in_play[remove]
            self.combat.players.remove(remove)

    def check_item(self, item_slug: str) -> int:
        item = self.player.find_item(item_slug)
        assert item
        return item.quantity

    def check_category(self, cat_slug: str) -> int:
        category = sum(
            [
                itm.quantity
                for itm in self.player.items
                if itm.category == cat_slug
            ]
        )
        return category

    def throw_tuxeball(self) -> None:
        tuxeball = self.player.find_item("tuxeball_park")
        if tuxeball:
            self.deliver_action(tuxeball)

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""
        choice = self.get_selected_item()
        if choice:
            self.description = choice.description

        def choose_item() -> None:
            # open menu to choose item
            menu = self.client.push_state(ItemMenuState())
            # set next menu after the selection is made
            menu.is_valid_entry = validate  # type: ignore[assignment]
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def validate(item: Optional[Item]) -> bool:
            ret = False
            if item:
                ret = (
                    True
                    if (
                        item.category == ItemCategory.doll
                        and self.description == "menu_doll"
                    )
                    or (
                        item.category == ItemCategory.food
                        and self.description == "menu_food"
                    )
                    else False
                )
            return ret

        def choose_target(menu_item: MenuItem[Item]) -> None:
            # open menu to choose target of item
            item = menu_item.game_object
            self.deliver_action(item)
            self.client.pop_state()

        choose_item()

    def deliver_action(self, item: Item) -> None:
        enemy = self.opponents[0]
        self.combat.enqueue_action(self.player, item, enemy)
        self.client.pop_state()
