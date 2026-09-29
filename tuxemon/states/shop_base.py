# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
)

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.economy.applier import EconomyApplier
from tuxemon.economy.transaction import TransactionManager
from tuxemon.entity.npc import NPC
from tuxemon.item.shop_utils import calc_internal_rect
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons
from tuxemon.platform.const.sizes import MAX_MENU_ITEMS
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.economy.economy import Economy


class ShopAsset(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...


T = TypeVar("T", bound=ShopAsset)


class ShopMenuState(Menu[T], Generic[T], ABC):
    """
    A generic shop menu state that can handle any type of asset.
    All shared logic is implemented here. Subclasses provide the specific
    details for their respective asset types.
    """

    name: ClassVar[str] = "ShopMenuState"
    draw_borders = False

    def __init__(
        self,
        client: BaseClient,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)

        # This sprite is used to display the selected asset.
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.asset_sprite = Sprite()
        self.sprites.add(self.asset_sprite)

        self.menu_items.line_spacing = self.scale_int(7)
        self.page_size = MAX_MENU_ITEMS
        self.current_page = 0
        self.total_pages = 0
        self.inventory: list[T] = []

        # This is the area where the asset's description is displayed.
        rect = self.client.context.rect.copy()
        rect.top = self.scale_int(106)
        rect.left = self.scale_int(3)
        rect.width = self.scale_int(250)
        rect.height = self.scale_int(32)
        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=rect,
            scaling=self.client.context.scaling,
        )
        self.sprites.add(self.text_area, layer=100)

        self.image_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.buyer = buyer
        self.seller = seller
        self.economy = economy
        self.applier = EconomyApplier()
        self.buyer_manager = self.buyer.money_controller.money_manager
        self.seller_manager = self.seller.money_controller.money_manager
        self.transaction_manager = TransactionManager(
            self.buyer_manager, self.seller_manager, self.client.shop_manager
        )

    def calc_internal_rect(self) -> Rect:
        return calc_internal_rect(self.rect)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        asset = self.get_selected_item()
        if asset:
            image = self._get_asset_image(asset)
            if image:
                self.asset_sprite.image = image
                self.asset_sprite.rect = image.get_rect(
                    center=self.image_center
                )
            self._display_asset_description(asset)

    def _add_menu_item(
        self,
        asset: T,
        label: str,
        metadata: dict[str, Any],
        unavailable: bool = False,
    ) -> None:
        """Helper to create and add a MenuItem for an asset with shared styling."""
        fg = self.unavailable_color_shop if unavailable else None
        image = self.shadow_text(label, fg=fg)
        menu_item = MenuItem(
            image, asset.name, asset.description, asset, not unavailable
        )
        menu_item.metadata.update(metadata)
        self.add(menu_item)

    @abstractmethod
    def _get_asset_image(self, asset: MenuItem[T]) -> Surface | None:
        """Returns the visual representation for the asset."""

    @abstractmethod
    def _display_asset_description(self, asset: MenuItem[T]) -> None:
        """Displays the description for the asset."""

    @abstractmethod
    def _filter_inventory(self) -> list[T]:
        """Returns the filtered list of assets for the shop."""

    @abstractmethod
    def _populate_menu(self, inventory: list[T]) -> None:
        """Populates the menu with assets based on a provided inventory list."""

    @abstractmethod
    def _get_selection_menu_params(
        self, menu_item: MenuItem[T]
    ) -> dict[str, Any]:
        """Provides parameters for the transaction menu."""

    def initialize_items(self) -> Generator[MenuItem[T], None, None]:
        self.inventory = self._filter_inventory()
        if not self.inventory:
            return

        # Compute total pages
        if self.page_size:
            self.total_pages = max(
                1, math.ceil(len(self.inventory) / self.page_size)
            )
        else:
            self.total_pages = 1

        # Clamp current page
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        # Slice items for this page
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_inventory = self.inventory[start:end]

        self._populate_menu(paged_inventory)
        yield from self.menu_items

    def reload_shop(self) -> None:
        self.clear()
        self.inventory = self._filter_inventory()

        # Recompute total pages
        if self.page_size:
            self.total_pages = max(
                1, math.ceil(len(self.inventory) / self.page_size)
            )
        else:
            self.total_pages = 1

        # Clamp current page
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        # Slice items for this page
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_inventory = self.inventory[start:end]

        self._populate_menu(paged_inventory)
        self.selected_index = (
            min(self.selected_index, len(self.menu_items) - 1)
            if self.menu_items
            else -1
        )
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        total_pages = self.total_pages

        if event.button == buttons.RIGHT and event.pressed:
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.reload_shop()
            return None
        elif event.button == buttons.LEFT and event.pressed:
            if self.current_page > 0:
                self.current_page -= 1
                self.reload_shop()
            return None

        return super().process_event(event)

    def on_menu_selection(self, menu_item: MenuItem[T]) -> None:
        """Handles the common logic for pushing the quantity menu."""
        params = self._get_selection_menu_params(menu_item)

        self.client.state_manager.push_state(
            "QuantityPickerState",
            client=self.client,
            min_value=1,
            max_value=params["max_quantity"],
            start_value=1,
            step=1,
            callback=params["callback"],
            cost=params["cost"],
            wallet_money=params.get("wallet_money"),
        )
