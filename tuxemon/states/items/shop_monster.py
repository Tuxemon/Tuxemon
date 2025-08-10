# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Optional

from pygame.rect import Rect

from tuxemon import prepare, tools
from tuxemon.item.item import INFINITE_ITEMS
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.menu.quantity import QuantityAndCostMenu, QuantityAndPriceMenu
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.states.items.shop_utils import (
    TransactionManager,
    calc_internal_rect,
    filter_party,
    generate_label,
)
from tuxemon.ui.paginator import Paginator
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.economy.economy import Economy
    from tuxemon.npc import NPC


class ShopMonsterMenuState(Menu[Monster]):

    name: ClassVar[str] = "ShopMonsterMenuState"
    draw_borders = False

    def __init__(
        self,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        buyer_purge: bool = False,
    ) -> None:
        super().__init__()

        # this sprite is used to display the monster
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.monster_sprite = Sprite()
        self.sprites.add(self.monster_sprite)

        self.menu_items.line_spacing = tools.scale(7)
        self.current_page = 0
        self.total_pages = 0
        self.inventory: list[Monster] = []

        # this is the area where the monster description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        self.image_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.buyer = buyer
        self.seller = seller
        self.buyer_purge = buyer_purge
        self.economy = economy
        self.update_background(self.economy.model.background)
        self.buyer_manager = self.buyer.money_controller.money_manager
        self.seller_manager = self.seller.money_controller.money_manager
        self.transaction_manager = TransactionManager(
            self.buyer_manager, self.seller_manager
        )
        self.paginator = Paginator(self.inventory, prepare.MAX_MENU_ITEMS)

    def calc_internal_rect(self) -> Rect:
        return calc_internal_rect(self.rect)

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        """Check if the selected monster is valid for purchase or sale."""
        if not monster:
            return False
        if self.buyer.isplayer:
            _, _, price = generate_label(monster, self.economy, 1)
            wallet = self.buyer_manager.get_money()
            key = f"{self.economy.model.slug}:{monster.slug}"
            qty = self.buyer.game_variables.get(key, 0)
            if price > wallet or qty == 0:
                return False
        if self.seller.isplayer:
            if self.seller.party.party_size == 1:
                return False
        return True

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        monster = self.get_selected_item()
        if monster:
            image = monster.game_object.get_sprite("front")
            assert image
            self.monster_sprite.image = image.image
            self.monster_sprite.rect = image.image.get_rect(
                center=self.image_center
            )
            if monster.description:
                self.dialog.alert(monster.description, dialog_speed="max")

    def generate_monster_label(
        self,
        monster: Monster,
        qty: Optional[int] = None,
        seller_mode: bool = False,
    ) -> tuple[str, str, int]:
        """Generate the label for shop monsters, handling both buyer and seller modes."""
        return generate_label(monster, self.economy, qty, seller_mode)

    def _populate_menu_monsters(
        self, inventory: list[Monster]
    ) -> Generator[MenuItem[Monster], None, None]:
        for monster in inventory:
            if self.buyer.isplayer:
                key = f"{self.economy.model.slug}:{monster.slug}"
                qty = self.buyer.game_variables.get(key, 0)
                label, discount, price = self.generate_monster_label(
                    monster, qty
                )
                fg = (
                    self.unavailable_color_shop
                    if price > self.buyer_manager.get_money()
                    else None
                )
                image = self.shadow_text(label, fg=fg)
                menu_monster = MenuItem(
                    image, monster.name, monster.description, monster
                )
                yield menu_monster
                menu_monster.metadata["price"] = price
                self.add(menu_monster)
            elif self.seller.isplayer:
                label, discount, cost = self.generate_monster_label(
                    monster, qty=None, seller_mode=True
                )
                image = self.shadow_text(label)
                menu_monster = MenuItem(
                    image, monster.name, monster.description, monster
                )
                yield menu_monster
                menu_monster.metadata["cost"] = cost
                self.add(menu_monster)

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        self.inventory = filter_party(self.buyer, self.seller, self.economy)
        if not self.inventory:
            return

        self.paginator.update_items(self.inventory)
        self.total_pages = self.paginator.total_pages()
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        paged_inventory = self.paginator.paginate(self.current_page)
        yield from self._populate_menu_monsters(paged_inventory)

    def reload_shop(self) -> None:
        self.clear()
        self.inventory = filter_party(self.buyer, self.seller, self.economy)

        paged_inventory = self.paginator.paginate(self.current_page)
        # Force generator execution
        list(self._populate_menu_monsters(paged_inventory))

        self.selected_index = (
            min(self.selected_index, len(self.menu_items) - 1)
            if self.menu_items
            else -1
        )
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        total_pages = self.paginator.total_pages()

        if event.button == buttons.RIGHT and event.pressed:
            # Move to the next page if possible
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.reload_shop()
        elif event.button == buttons.LEFT and event.pressed:
            # Move to the previous page if possible
            if self.current_page > 0:
                self.current_page -= 1
                self.reload_shop()
        else:
            return super().process_event(event)

        return None


class ShopMonsterBuyMenuState(ShopMonsterMenuState):
    """State for buying monsters."""

    name: ClassVar[str] = "ShopMonsterBuyMenuState"

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        price: int = menu_monster.metadata.get("price", 1)
        label = f"{self.economy.model.slug}:{monster.slug}"

        def buy_monster(quantity: int) -> None:
            self.transaction_manager.buy_monster(
                self.buyer, monster, quantity, label, price
            )
            self.reload_items()
            if (
                self.seller.shop_inventory
                and not self.seller.shop_inventory.has_monster(monster.slug)
            ):
                self.on_menu_selection_change()

        money = self.buyer_manager.get_money()
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables.get(label, INFINITE_ITEMS)
        max_quantity = (
            qty_can_afford
            if inventory == INFINITE_ITEMS
            else min(qty_can_afford, inventory)
        )

        self.client.push_state(
            QuantityAndPriceMenu(
                callback=partial(buy_monster),
                max_quantity=max_quantity,
                quantity=1,
                shrink_to_items=True,
                price=price,
            )
        )


class ShopMonsterSellMenuState(ShopMonsterMenuState):
    """State for selling monsters."""

    name: ClassVar[str] = "ShopMonsterSellMenuState"

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        metadata_cost = menu_monster.metadata.get("cost")
        basic_cost = self.economy.lookup_item_field(monster.slug, "cost")

        if metadata_cost is not None:
            cost = metadata_cost
        elif basic_cost:
            cost = basic_cost
        else:
            cost = round(monster.hp * self.economy.model.resale_multiplier)

        def sell_monster(quantity: int) -> None:
            self.transaction_manager.sell_monster(self.seller, monster, cost)
            self.reload_items()
            if not self.seller.party.has_monster(monster):
                self.on_menu_selection_change()

        self.client.push_state(
            QuantityAndCostMenu(
                callback=partial(sell_monster),
                max_quantity=1,
                quantity=1,
                shrink_to_items=True,
                cost=cost,
            )
        )
