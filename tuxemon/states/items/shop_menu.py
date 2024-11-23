# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.quantity import QuantityAndCostMenu, QuantityAndPriceMenu
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.economy import Economy
    from tuxemon.npc import NPC

INFINITE_ITEMS = prepare.INFINITE_ITEMS


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class ShopMenuState(PygameMenuState):

    def __init__(
        self,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
    ) -> None:
        theme = self._setup_theme(economy.model.background)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        width, height = prepare.SCREEN_SIZE

        super().__init__(height=height, width=width)

        self.buyer = buyer
        self.seller = seller
        self.economy = economy

        self.add_menu_items(self.menu, self.buyer, self.seller, self.economy)
        self.reset_theme()

    def add_menu_items(
        self, menu: pygame_menu.Menu, buyer: NPC, seller: NPC, economy: Economy
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        menu._width = int(width * 0.9)

        shop_name = T.translate(economy.model.slug)
        menu.add.label(shop_name, selectable=True)
        menu.add.vertical_margin(25)
        if buyer.isplayer:
            self.add_buy_menu_items(menu, buyer, seller, economy)
        elif seller.isplayer:
            self.add_sell_menu_items(menu, buyer, seller, economy)
        menu.add.vertical_margin(25)
        menu.add.label(shop_name, selectable=True)

    def add_buy_menu_items(
        self, menu: pygame_menu.Menu, buyer: NPC, seller: NPC, economy: Economy
    ) -> None:
        def add_item_to_menu(item: Item, quantity: int) -> None:
            wallet = buyer.money["player"]
            price = economy.get_item_field(item.slug, "price")
            button = price <= wallet and (
                item.quantity == INFINITE_ITEMS or quantity > 0
            )

            label = f"${price:4} {item.name}"
            if item.quantity != INFINITE_ITEMS:
                label += f" x {quantity}"
            if not button:
                label = f"${price:4} {T.translate('shop_buy_soldout')}"

            new_image = self._create_image(item.sprite)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.image(new_image)

            if button:
                menu.add.button(
                    title=label,
                    action=partial(self.on_buy, item),
                    font_size=self.font_size_small,
                    align=locals.ALIGN_CENTER,
                    selection_effect=HighlightSelection(),
                )
            else:
                menu.add.label(
                    title=label,
                    font_size=self.font_size_small,
                    align=locals.ALIGN_CENTER,
                )

            menu.add.label(
                item.description,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                wordwrap=True,
            )

        def add_monster_to_menu(monster: Monster, quantity: int) -> None:
            wallet = buyer.money["player"]
            price = economy.get_monster_field(monster.slug, "price")
            button = price <= wallet and quantity > 0

            label = f"${price:4} {monster.name} lv {monster.level}"
            if quantity > 0:
                label += f" x {quantity}"
            if not button:
                label = f"${price:4} {T.translate('shop_buy_soldout')}"

            path = f"gfx/sprites/battle/{monster.slug}-front.png"
            new_image = self._create_image(path)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.image(new_image)

            if button:
                menu.add.button(
                    title=label,
                    action=partial(self.on_buy_monster, monster),
                    font_size=self.font_size_small,
                    align=locals.ALIGN_CENTER,
                    selection_effect=HighlightSelection(),
                )
            else:
                menu.add.label(
                    title=label,
                    font_size=self.font_size_small,
                    align=locals.ALIGN_CENTER,
                )

            menu.add.label(
                monster.description,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                wordwrap=True,
            )

        items = seller.item_boxes.get_items(economy.model.slug)
        if items:
            items = sorted(
                items, key=lambda x: economy.get_item_field(x.slug, "price")
            )
            for item in items:
                key = f"{economy.model.slug}:{item.slug}"
                quantity = buyer.game_variables[key]
                add_item_to_menu(item, quantity)

        monsters = seller.monster_boxes.get_monsters(economy.model.slug)
        if monsters:
            monsters = sorted(
                monsters,
                key=lambda x: economy.get_monster_field(x.slug, "price"),
            )
            for monster in monsters:
                key = f"{economy.model.slug}:{monster.slug}"
                quantity = buyer.game_variables[key]
                add_monster_to_menu(monster, quantity)

    def add_sell_menu_items(
        self, menu: pygame_menu.Menu, buyer: NPC, seller: NPC, economy: Economy
    ) -> None:
        inventory = [
            item
            for item in seller.items
            for t in economy.model.items
            if item.slug == t.name
        ]

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        # when the player sells, sort based on cost
        inventory = sorted(
            inventory, key=lambda x: economy.lookup_item_cost(x.slug)
        )

        for item in inventory:
            self.cost = self.economy.lookup_item_cost(item.slug)
            if item.quantity != INFINITE_ITEMS:
                label = f"${self.cost:3} {item.name} x {item.quantity}"
            else:
                label = f"${self.cost:3} {item.name}"
            new_image = self._create_image(item.sprite)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.image(new_image)
            menu.add.button(
                title=label,
                action=partial(self.on_sell, item),
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )
            menu.add.label(
                item.description,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                wordwrap=True,
            )

    def on_buy(self, item: Item) -> None:
        """
        Called when player has selected something from the shop's inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            item: Selected item.

        """
        price = self.economy.lookup_item_price(item.slug)
        label = f"{self.economy.model.slug}:{item.slug}"

        def buy_item(itm: Item, quantity: int) -> None:
            if not quantity:
                return

            in_bag = self.buyer.find_item(itm.slug)
            if in_bag:
                # reduces quantity only no-infinite items
                if itm.quantity != INFINITE_ITEMS:
                    itm.quantity -= quantity
                    self.buyer.game_variables[label] -= quantity
                in_bag.quantity += quantity
            else:
                if itm.quantity != INFINITE_ITEMS:
                    itm.quantity -= quantity
                    self.buyer.game_variables[label] -= quantity
                new_buy = Item()
                new_buy.load(itm.slug)
                new_buy.quantity = quantity
                self.buyer.add_item(new_buy)
            self.buyer.money["player"] -= quantity * price
            self.client.replace_state(
                ShopMenuState(self.buyer, self.seller, self.economy)
            )

        money = self.buyer.money["player"]
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables[label]
        _inventory = 99999 if inventory == INFINITE_ITEMS else inventory
        max_quantity = min(_inventory, qty_can_afford)

        self.client.push_state(
            QuantityAndPriceMenu(
                callback=partial(buy_item, item),
                max_quantity=max_quantity,
                quantity=1,
                shrink_to_items=True,
                price=price,
            )
        )

    def on_buy_monster(self, monster: Monster) -> None:
        """
        Called when player has selected something from the shop's inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            monster: Selected monster.

        """
        price = self.economy.get_monster_field(monster.slug, "price")
        level = self.economy.get_monster_field(monster.slug, "level")
        label = f"{self.economy.model.slug}:{monster.slug}"

        def buy_monster(monster: Monster, quantity: int) -> None:
            if not quantity:
                return

            self.buyer.game_variables[label] -= quantity
            self.buyer.add_monster(monster, len(self.buyer.monsters))
            self.buyer.money["player"] -= quantity * price
            self.client.replace_state(
                ShopMenuState(self.buyer, self.seller, self.economy)
            )

        money = self.buyer.money["player"]
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables[label]
        _inventory = 99999 if inventory == INFINITE_ITEMS else inventory
        max_quantity = min(_inventory, qty_can_afford)

        self.client.push_state(
            QuantityAndPriceMenu(
                callback=partial(buy_monster, monster),
                max_quantity=max_quantity,
                quantity=1,
                shrink_to_items=True,
                price=price,
            )
        )

    def on_sell(self, item: Item) -> None:
        """
        Called when player has selected something from the inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.

        """
        cost = self.economy.lookup_item_cost(item.slug)

        def sell_item(itm: Item, quantity: int) -> None:
            if not quantity:
                return

            diff = itm.quantity - quantity
            if diff <= 0:
                self.seller.remove_item(itm)
            else:
                itm.quantity = diff

            if self.seller.money.get("player") is not None:
                self.seller.money["player"] += quantity * cost
            self.client.replace_state(
                ShopMenuState(self.buyer, self.seller, self.economy)
            )

        self.client.push_state(
            QuantityAndCostMenu(
                callback=partial(sell_item, item),
                max_quantity=item.quantity,
                quantity=1,
                shrink_to_items=True,
                cost=cost,
            )
        )
