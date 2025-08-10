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
        self.item = item

    def set_item(self, item: Item) -> None:
        if item.behaviors.holdable:
            self.item = item
        else:
            logger.error(f"{item.name} can't be held")

    def get_item(self) -> Optional[Item]:
        return self.item

    def has_item(self) -> bool:
        return self.item is not None

    def clear_item(self) -> None:
        self.item = None

    def encode_item(self) -> Mapping[str, Any]:
        return self.item.get_state() if self.item is not None else {}

    def decode_item(
        self, json_data: Optional[Mapping[str, Any]]
    ) -> Optional[Item]:
        return Item(save_data=json_data) if json_data is not None else None
