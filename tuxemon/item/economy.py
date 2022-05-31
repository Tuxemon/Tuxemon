#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#
# economy Economy handling module.
#
#

from __future__ import annotations
import logging

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
            results = db.lookup(slug, table="economy").dict()
        except KeyError:
            raise RuntimeError(f"Failed to find economy with slug {slug}")

        self.slug = results["slug"]
        self.items = results["items"]

    def lookup_item_field(self, item_slug: str, field: str) -> int:
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
            if item["item_name"] == item_slug and field in item:
                value = item[field]
                return value

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

        if not price:
            raise RuntimeError(
                f"Price for item '{item_slug}' not found in " f"economy '{self.slug}'"
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

        if not cost:
            raise RuntimeError(
                f"Cost for item '{item_slug}' not found in " f"economy '{self.slug}'"
            )

        return cost
