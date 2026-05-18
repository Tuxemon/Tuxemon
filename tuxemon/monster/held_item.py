# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from tuxemon.item.item import Item

logger = logging.getLogger(__name__)


class MonsterItemHandler:
    def __init__(self, item: Item | None = None):
        self._item = item

    @property
    def held_item(self) -> Item | None:
        return self._item

    def set_item(self, item: Item) -> bool:
        if item.behaviors.holdable:
            self._item = item
            return True
        else:
            logger.error(f"{item.name} can't be held")
            return False

    def take_item(self) -> Item | None:
        item = self._item
        self._item = None
        return item

    def has_item(self) -> bool:
        return self._item is not None

    def clear_item(self) -> None:
        self._item = None

    def encode_item(self) -> Mapping[str, Any]:
        return self._item.get_state() if self._item is not None else {}

    def decode_item(self, json_data: Mapping[str, Any] | None) -> Item | None:
        return Item.from_save(json_data) if json_data is not None else None
