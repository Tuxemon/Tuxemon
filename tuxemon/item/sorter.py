# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.item.item import Item


class ItemSorter:
    def __init__(self, sort_order: list[str] | None = None) -> None:
        self.sort_order = sort_order or ["potion", "food", "utility", "quest"]
        self.sort_order_rank = {
            category: i for i, category in enumerate(self.sort_order)
        }

    def rank_item(self, item: Item) -> tuple[int, str]:
        rank = self.sort_order_rank.get(item.sort, len(self.sort_order))
        return rank, item.name.lower()

    def sort(self, items: Sequence[Item]) -> Sequence[Item]:
        return sorted(items, key=self.rank_item)

    def set_sort_order(self, new_order: list[str]) -> None:
        self.sort_order = new_order
        self.sort_order_rank = {
            category: i for i, category in enumerate(new_order)
        }
