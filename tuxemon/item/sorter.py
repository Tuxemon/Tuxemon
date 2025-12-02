# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuxemon.item.item import Item


class ItemSorter:
    def __init__(
        self, mode: str = "category", sort_order: Optional[list[str]] = None
    ) -> None:
        self.mode = mode
        self.sort_order = sort_order or ["potion", "food", "utility", "quest"]
        self.sort_order_rank = {
            cat: i for i, cat in enumerate(self.sort_order)
        }

    def rank_item(self, item: Item) -> tuple[int, str]:
        rank = self.sort_order_rank.get(item.sort, len(self.sort_order))
        return rank, item.name.lower()

    def sort(self, items: Sequence[Item]) -> Sequence[Item]:
        if self.mode == "category":
            return sorted(items, key=self.rank_item)
        elif self.mode == "name":
            return sorted(items, key=lambda i: i.name.lower())
        elif self.mode == "quantity":
            return sorted(items, key=lambda i: i.quantity, reverse=True)
        elif self.mode == "cost":
            return sorted(items, key=lambda i: i.cost, reverse=True)
        return items

    def set_mode(self, mode: str) -> None:
        self.mode = mode
