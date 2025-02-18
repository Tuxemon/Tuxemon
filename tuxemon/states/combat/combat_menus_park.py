# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Optional

from tuxemon.db import ItemCategory
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.monster import Monster
from tuxemon.states.items.item_menu import ItemMenuState

if TYPE_CHECKING:
    from tuxemon.states.combat.combat import CombatState


MenuGameObj = Callable[[], None]


class MainParkMenuState(PopUpMenu[MenuGameObj]):
    """
    Main menu Park: ball, food, doll and run

    """

    escape_key_exits = False
    columns = 2

    def __init__(self, cmb: CombatState, monster: Monster) -> None:
        super().__init__()
        self.combat = cmb
        self.player = cmb.players[0]  # human
        self.enemy = cmb.players[1]  # ai
        self.monster = monster
        self.opponents = cmb.monsters_in_play[self.enemy]
        self.description: Optional[str] = None

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        del self.combat.hud[self.monster]
        self.combat.update_hud(self.player, False)
        menu_items_map = (
            ("menu_ball", self.throw_tuxeball),
            ("menu_food", self.open_item_menu),
            ("menu_doll", self.open_item_menu),
            ("menu_run", self.run),
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            itm = 1
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
            menu = self.client.push_state(ItemMenuState())
            menu.is_valid_entry = validate  # type: ignore[assignment]
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def validate(item: Optional[Item]) -> bool:
            ret = False
            if item and item.category == ItemCategory.potion:
                if self.description == "menu_doll":
                    ret = True
                if self.description == "menu_food":
                    ret = True
            return ret

        def choose_target(menu_item: MenuItem[Item]) -> None:
            item = menu_item.game_object
            self.deliver_action(item)
            self.client.pop_state()

        choose_item()

    def deliver_action(self, item: Item) -> None:
        enemy = self.opponents[0]
        self.combat.enqueue_action(self.player, item, enemy)
        self.client.pop_state()
