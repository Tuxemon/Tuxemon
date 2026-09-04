# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from tuxemon.item.item import Item
from tuxemon.locale.locale import T

logger = logging.getLogger(__name__)

# Translation keys explaining why a monster refused to hold an item.
NOT_HOLDABLE = "held_item_not_holdable"
UNSUITABLE_HOLDER = "held_item_unsuitable"


@dataclass(frozen=True)
class EquipResult:
    """
    Outcome of trying to give an item to a monster to hold.

    Attributes:
        success: Whether the monster is now holding the item.
        reason: A translated, player-facing explanation of a refusal, or
            ``None`` when the item was accepted.
        msgid: The translation key behind ``reason``, so callers can tell
            refusals apart without matching on translated text.
    """

    success: bool
    reason: str | None = None
    msgid: str | None = None

    def __bool__(self) -> bool:
        return self.success

    @classmethod
    def accepted(cls) -> EquipResult:
        return cls(True)

    @classmethod
    def refused(
        cls, msgid: str, monster_name: str, item_name: str
    ) -> EquipResult:
        params = {"name": monster_name, "item": item_name}
        return cls(False, T.format(msgid, params), msgid)


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
