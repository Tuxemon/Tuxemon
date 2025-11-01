# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from tuxemon import prepare
from tuxemon.boxes import ItemBoxes
from tuxemon.item.item import decode_items, encode_items

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.npc import NPC
    from tuxemon.save_state import NPCState


logger = logging.getLogger(__name__)


class BagHandler:

    def __init__(
        self,
        item_boxes: ItemBoxes,
        owner: NPC,
        items: Optional[list[Item]] = None,
        bag_limit: int = prepare.MAX_TYPES_BAG,
    ) -> None:
        self._owner = owner
        self._items = items if items is not None else []
        self._bag_limit = bag_limit
        self._item_boxes = item_boxes

    @property
    def owner(self) -> NPC:
        return self._owner

    @property
    def items(self) -> list[Item]:
        return self._items

    def add_item(
        self, item: Item, quantity: int = 1, locker: str = prepare.LOCKER
    ) -> None:
        """
        Adds an item to the NPC's bag.

        If the bag is full (based on MAX_TYPES_BAG), it will send the item to
        the PCState archive (item boxes).
        """
        logger.debug(
            f"Adding item '{item.slug}' (quantity: {quantity}) to NPC's inventory."
        )

        if not self._item_boxes.has_box(locker, "item"):
            logger.debug(
                f"Item box '{locker}' does not exist. Creating new item box."
            )
            self._item_boxes.create_box(locker, "item")

        existing = self.find_item(item.slug)
        if existing:
            new_qty = existing.quantity + quantity
            logger.debug(
                f"Item '{item.slug}' exists in inventory. Increasing quantity from {existing.quantity} to {new_qty}."
            )
            existing.set_quantity(new_qty)
        elif len(self._items) >= self._bag_limit:
            logger.debug(
                f"Bag is full. Sending item '{item.slug}' to item box '{locker}'."
            )
            item.set_quantity(quantity)
            self._item_boxes.add_item(locker, item)
        else:
            logger.debug(
                f"Item '{item.slug}' added to bag. Current total items: {len(self._items) + 1}."
            )
            item.set_quantity(quantity)
            self._items.append(item)

    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        """
        Removes a quantity of an item from the NPC's bag.

        If quantity reaches zero or below, the item is fully removed.
        """
        logger.debug(
            f"Attempting to remove {quantity} of '{item.slug}' from inventory."
        )

        if quantity < 0:
            logger.warning(
                f"Tried to remove negative quantity: {quantity} for item '{item.slug}'"
            )
            return False

        if item in self._items:
            if item.quantity <= quantity:
                logger.debug(
                    f"Removing item '{item.slug}' completely (quantity: {item.quantity})."
                )
                self._items.remove(item)
            else:
                new_qty = item.quantity - quantity
                logger.debug(
                    f"Reducing quantity of '{item.slug}' from {item.quantity} to {new_qty}."
                )
                item.set_quantity(new_qty)
            return True
        logger.debug(f"Item '{item.slug}' not found in inventory.")
        return False

    def find_item(self, item_slug: str) -> Optional[Item]:
        """
        Finds the first item in the NPC's bag with the given slug.
        """
        for itm in self._items:
            if itm.slug == item_slug:
                return itm
        return None

    def has_item(self, item_slug: str) -> bool:
        """
        Checks if the NPC's bag contains an item with the given slug.
        """
        return any(itm.slug == item_slug for itm in self._items)

    def find_item_by_id(self, instance_id: UUID) -> Optional[Item]:
        """
        Finds an item in the NPC's bag which has the given instance ID.
        """
        return next(
            (itm for itm in self._items if itm.instance_id == instance_id),
            None,
        )

    def clear_items(self) -> None:
        """Removes all items from the NPC's bag."""
        self._items.clear()

    def get_all_item_quantities(self) -> dict[str, int]:
        """
        Returns a dictionary mapping item slugs to their total quantities
        in the NPC's bag. This provides a 'count-based view' of the bag.
        """
        quantities: dict[str, int] = {}
        for item in self._items:
            quantities[item.slug] = item.quantity
        return quantities

    def encode_items(self) -> Sequence[Mapping[str, Any]]:
        return encode_items(self._items)

    def decode_items(self, json_data: Optional[NPCState]) -> None:
        if json_data and json_data.items is not None:
            self._items = [itm for itm in decode_items(json_data.items)]
