# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tuxemon.boxes import ItemBoxes
from tuxemon.item.item import Item, decode_items, encode_items
from tuxemon.platform.const.sizes import LOCKER, MAX_TYPES_BAG

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.save_system.save_state import NPCState

logger = logging.getLogger(__name__)


class BagHandler:
    """Manages an NPC's inventory and coordinates overflow with item boxes."""

    def __init__(
        self,
        item_boxes: ItemBoxes,
        owner: NPC,
        items: list[Item] | None = None,
        bag_limit: int = MAX_TYPES_BAG,
    ) -> None:
        self._owner = owner
        self._items: list[Item] = items or []
        self._bag_limit = bag_limit
        self._item_boxes = item_boxes

    @property
    def owner(self) -> NPC:
        return self._owner

    @property
    def items(self) -> list[Item]:
        return self._items

    @property
    def is_full(self) -> bool:
        return len(self._items) >= self._bag_limit

    def add_item(
        self, item: Item, quantity: int = 1, locker: str = LOCKER
    ) -> bool:
        """Add an item to the bag, or send to a box if full. Returns True on success."""
        logger.debug(f"Adding '{item.slug}' x{quantity} to inventory.")

        if quantity <= 0:
            logger.warning(f"Ignoring non-positive quantity: {quantity}")
            return False

        if not self._item_boxes.has_box(locker, "item"):
            logger.debug(f"Item box '{locker}' missing; creating.")
            self._item_boxes.create_box(locker)

        existing = self.find_item(item.slug)
        if existing:
            logger.debug(
                f"Item '{item.slug}' exists. Increasing quantity "
                f"{existing.quantity} → {existing.quantity + quantity}."
            )
            existing.increase_quantity(quantity)
            return True

        if self.is_full:
            logger.debug(
                f"Bag full. Sending '{item.slug}' x{quantity} to box '{locker}'."
            )
            item.set_quantity(quantity)
            self._item_boxes.add_item(locker, item)
            return True

        logger.debug(f"Adding new item '{item.slug}' to bag.")
        item.set_quantity(quantity)
        self._items.append(item)
        return True

    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        """Remove quantity of an item; remove entirely if quantity reaches zero."""
        logger.debug(f"Removing '{item.slug}' x{quantity} from inventory.")

        if quantity < 0:
            logger.warning(f"Negative quantity removal attempted: {quantity}")
            return False

        if item not in self._items:
            logger.debug(f"Item '{item.slug}' not found in bag.")
            return False

        if item.quantity == 0:
            self._items.remove(item)
            return True

        # Try to remove from stock
        if not item.stock.try_remove(quantity):
            logger.debug(
                f"Not enough quantity of '{item.slug}' to remove {quantity}."
            )
            return False

        # Remove item entirely if empty
        if not item.stock.has_any:
            logger.debug(f"Removing item '{item.slug}' completely.")
            self._items.remove(item)
        else:
            logger.debug(
                f"Reducing '{item.slug}' quantity to {item.quantity}."
            )

        return True

    def find_item(self, slug: str) -> Item | None:
        return next((itm for itm in self._items if itm.slug == slug), None)

    def has_item(self, slug: str) -> bool:
        return any(itm.slug == slug for itm in self._items)

    def find_item_by_id(self, instance_id: UUID) -> Item | None:
        return next(
            (itm for itm in self._items if itm.instance_id == instance_id),
            None,
        )

    def clear_items(self) -> None:
        logger.debug("Clearing all items from bag.")
        self._items.clear()

    def _validate_index(self, index: int) -> None:
        if not (0 <= index < len(self._items)):
            raise IndexError("Index out of bounds for bag items.")

    def swap_items(self, index_1: int, index_2: int) -> None:
        self._validate_index(index_1)
        self._validate_index(index_2)
        logger.debug(f"Swapping items at positions {index_1} and {index_2}.")
        self._items[index_1], self._items[index_2] = (
            self._items[index_2],
            self._items[index_1],
        )

    def get_all_item_quantities(self) -> dict[str, int]:
        return {item.slug: item.quantity for item in self._items}

    def encode_items(self) -> Sequence[Mapping[str, Any]]:
        return encode_items(self._items)

    def decode_items(self, json_data: NPCState | None) -> None:
        if not json_data or not json_data.items:
            return
        self._items = list(decode_items(json_data.items))
