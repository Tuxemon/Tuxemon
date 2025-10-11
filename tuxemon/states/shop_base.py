# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Optional,
    Protocol,
    TypeVar,
)

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare, tools
from tuxemon.item.shop_utils import (
    TransactionManager,
    calc_internal_rect,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.menu.quantity import QuantityAndCostMenu
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.ui.paginator import Paginator
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.economy.economy import Economy


class ShopAsset(Protocol):
    name: str
    description: str


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
        buyer: NPC,
        seller: NPC,
        economy: Economy,
    ) -> None:
        super().__init__()

        # This sprite is used to display the selected asset.
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.asset_sprite = Sprite()
        self.sprites.add(self.asset_sprite)

        self.menu_items.line_spacing = tools.scale(7)
        self.current_page = 0
        self.total_pages = 0
        self.inventory: list[T] = []

        # This is the area where the asset's description is displayed.
        rect = prepare.SCREEN_RECT.copy()
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
    def _get_asset_image(self, asset: MenuItem[T]) -> Optional[Surface]:
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

        self.paginator.update_items(self.inventory)
        self.total_pages = self.paginator.total_pages()
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        paged_inventory = self.paginator.paginate(self.current_page)
        self._populate_menu(paged_inventory)
        yield from self.menu_items

    def reload_shop(self) -> None:
        self.clear()
        self.inventory = self._filter_inventory()
        paged_inventory = self.paginator.paginate(self.current_page)
        self._populate_menu(paged_inventory)
        self.selected_index = (
            min(self.selected_index, len(self.menu_items) - 1)
            if self.menu_items
            else -1
        )
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        total_pages = self.paginator.total_pages()
        if event.button == buttons.RIGHT and event.pressed:
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.reload_shop()
        elif event.button == buttons.LEFT and event.pressed:
            if self.current_page > 0:
                self.current_page -= 1
                self.reload_shop()
        else:
            return super().process_event(event)
        return None

    def on_menu_selection(self, menu_item: MenuItem[T]) -> None:
        """Handles the common logic for pushing the quantity menu."""
        params = self._get_selection_menu_params(menu_item)
        self.client.state_manager.push_state(
            QuantityAndCostMenu(
                callback=params["callback"],
                max_quantity=params["max_quantity"],
                quantity=1,
                shrink_to_items=True,
                cost=params["cost"],
            )
        )
