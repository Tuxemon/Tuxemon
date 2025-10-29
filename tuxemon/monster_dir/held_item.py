# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional

from tuxemon.item.item import Item

logger = logging.getLogger(__name__)


class MonsterItemHandler:
    def __init__(self, item: Optional[Item] = None):
        self._item = item

    @property
    def held_item(self) -> Optional[Item]:
        return self._item

    def set_item(self, item: Item) -> bool:
        if item.behaviors.holdable:
            self._item = item
            return True
        else:
            logger.error(f"{item.name} can't be held")
            return False

    def take_item(self) -> Optional[Item]:
        item = self._item
        self._item = None
        return item

    def has_item(self) -> bool:
        return self._item is not None

    def clear_item(self) -> None:
        self._item = None

    def encode_item(self) -> Mapping[str, Any]:
        return self._item.get_state() if self._item is not None else {}

    def decode_item(
        self, json_data: Optional[Mapping[str, Any]]
    ) -> Optional[Item]:
        return Item(save_data=json_data) if json_data is not None else None
