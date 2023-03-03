# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.db import db

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
        for item in self.items:
            if item.item_name == item_slug and hasattr(item, field):
                return getattr(item, field)

        return None

    def lookup_item_price(self, item_slug: str) -> int:
        """Looks up the item price from this economy.

        The item is looked up by its slug.
        Raises a Runtime error if item's price is not found in this economy.

        Parameters:
            item_slug: The item slug to look up in this economy.

        Returns:
            Price of item for this economy.
        """
        price = self.lookup_item_field(item_slug, "price")

        if price is None:
            raise RuntimeError(
                f"Price for item '{item_slug}' not found in "
                f"economy '{self.slug}'"
            )

        return price

    def lookup_item_cost(self, item_slug: str) -> int:
        """Looks up the item cost from this economy.

        The item is looked up by its slug.
        Raises a Runtime error if item's cost is not found in this economy.

        Parameters:
            item_slug: The item slug to look up in this economy.

        Returns:
            Cost of item for this economy.
        """
        cost = self.lookup_item_field(item_slug, "cost")

        if cost is None:
            raise RuntimeError(
                f"Cost for item '{item_slug}' not found in "
                f"economy '{self.slug}'"
            )

        return cost

    def lookup_item_inventory(self, item_slug: str) -> int:
        """Looks up the item quantity from this economy.

        The item is looked up by its slug.
        Raises a Runtime error if item's inventory is not found in this economy.

        Parameters:
            item_slug: The item slug to look up in this economy.

        Returns:
            Quantity of items for this economy.
        """
        inventory = self.lookup_item_field(item_slug, "inventory")

        if inventory is None:
            raise RuntimeError(
                f"Quantity for item '{item_slug}' not found in "
                f"economy '{self.slug}'"
            )

        return inventory
