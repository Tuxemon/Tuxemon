# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any


class Paginator:
    @staticmethod
    def paginate(
        items: list[Any], page_size: int, page_number: int
    ) -> list[Any]:
        start = page_number * page_size
        end = start + page_size
        return items[start:end]

    @staticmethod
    def total_pages(items: list[Any], page_size: int) -> int:
        return -(-len(items) // page_size)

    @staticmethod
    def calculate_page_data(
        inventory: list[Any], current_page: int, page_size: int
    ) -> tuple[int, list[Any]]:
        total_pages = (len(inventory) + page_size - 1) // page_size
        start_index = current_page * page_size
        end_index = start_index + page_size
        page_items = inventory[start_index:end_index]
        return total_pages, page_items
