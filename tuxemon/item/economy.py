# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.db import EconomyItemModel, db
from tuxemon.item.item import Item

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class Economy:
    """An Economy holds a list of item names and their price/cost for this
    economy."""

    def __init__(self, slug: Optional[str] = None) -> None:
        # Auto-load the economy from the economy database.
        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads an economy from the economy.db database.

        The economy is looked up by its slug.

        Parameters:
            slug: The economy slug to look up in the economy.db database.

        """

        try:
            results = db.lookup(slug, table="economy")
        except KeyError:
            raise RuntimeError(f"Failed to find economy with slug {slug}")

        self.slug = results.slug
        self.items = results.items

    def lookup_item_field(self, item_slug: str, field: str) -> Optional[int]:
        """Looks up the item's field from this economy.

        The item and field is looked up by its slug.
        Returns None if field or item is not found.

        Parameters:
            item_slug: The item slug to look up in this economy.
            field: The field on item to get the value of.

        Returns:
            Field of item for this economy.
        """
        return self.get_item_field(item_slug, field)

    def lookup_item(self, item_slug: str, field: str) -> int:
        """Looks up the item's field from this economy.

        The item is looked up by its slug.
        Raises a Runtime error if item's field is not found in this economy.

        Parameters:
            item_slug: The item slug to look up in this economy.
            field: The field on item to get the value of.

        Returns:
            Field of item for this economy.
        """
        value = self.lookup_item_field(item_slug, field)

        if value is None:
            raise RuntimeError(
                f"{field.capitalize()} for item '{item_slug}' not found in "
                f"economy '{self.slug}'"
            )

        return value

    def lookup_item_price(self, item_slug: str) -> int:
        """Looks up the item price from this economy."""
        return self.lookup_item(item_slug, "price")

    def lookup_item_cost(self, item_slug: str) -> int:
        """Looks up the item cost from this economy."""
        return self.lookup_item(item_slug, "cost")

    def lookup_item_inventory(self, item_slug: str) -> int:
        """Looks up the item quantity from this economy."""
        return self.lookup_item(item_slug, "inventory")

    def update_item_quantity(self, item_slug: str, quantity: int) -> None:
        self.update_item_field(item_slug, "inventory", quantity)

    def get_item(self, item_slug: str) -> Optional[EconomyItemModel]:
        return next(
            (item for item in self.items if item.item_name == item_slug), None
        )

    def get_item_field(self, item_slug: str, field: str) -> Optional[int]:
        item = self.get_item(item_slug)
        if item and hasattr(item, field):
            return int(getattr(item, field))
        return None

    def update_item_field(
        self, item_slug: str, field: str, value: int
    ) -> None:
        item = self.get_item(item_slug)
        if item:
            setattr(item, field, value)
        else:
            raise RuntimeError(
                f"Item '{item_slug}' not found in economy '{self.slug}'"
            )

    def load_economy_items(self, character: NPC) -> list[Item]:
        items: list[Item] = []
        for item in self.items:
            label = f"{self.slug}:{item.item_name}"
            if label not in character.game_variables:
                character.game_variables[label] = self.get_item_field(
                    item.item_name, "inventory"
                )

            itm_in_shop = Item()
            if item.variables:
                if self.variable(item.variables, character):
                    itm_in_shop.load(item.item_name)
                    itm_in_shop.quantity = int(character.game_variables[label])
                    items.append(itm_in_shop)
            else:
                itm_in_shop.load(item.item_name)
                itm_in_shop.quantity = int(character.game_variables[label])
                items.append(itm_in_shop)
        return items

    def variable(self, variables: Sequence[str], character: NPC) -> bool:
        return all(
            parts[1] == character.game_variables.get(parts[0])
            for variable in variables
            if (parts := variable.split(":")) and len(parts) == 2
        )

    def add_economy_items_to_npc(
        self, character: NPC, items: list[Item]
    ) -> None:
        for item in items:
            character.add_item(item)
