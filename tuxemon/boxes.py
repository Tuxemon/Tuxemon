# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.item.item import decode_items, encode_items
from tuxemon.monster import decode_monsters, encode_monsters
from tuxemon.states.pc_kennel import HIDDEN_LIST
from tuxemon.states.pc_locker import HIDDEN_LIST_LOCKER

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPCState


class BoxCollection:
    def __init__(self) -> None:
        """
        Initializes a new BoxCollection instance.
        """
        self.item_boxes: dict[str, list[Item]] = {}
        self.monster_boxes: dict[str, list[Monster]] = {}

    def create_box(self, box_id: str, box_type: str) -> None:
        """
        Creates a new box with the given ID and type.

        Parameters:
            box_id: The ID of the box to create.
            box_type: The type of the box to create (either "item" or
                "monster").
        """
        if box_type == "item":
            self.item_boxes[box_id] = []
        elif box_type == "monster":
            self.monster_boxes[box_id] = []

    def add_item(self, box_id: str, item: Item) -> None:
        """
        Adds an item to the box with the given ID.

        Parameters:
            box_id: The ID of the box to add the item to.
            item: The item to add to the box.
        """
        if box_id not in self.item_boxes:
            self.create_box(box_id, "item")
        self.item_boxes[box_id].append(item)

    def add_monster(self, box_id: str, monster: Monster) -> None:
        """
        Adds a monster to the box with the given ID.

        Parameters:
            box_id: The ID of the box to add the monster to.
            monster: The monster to add to the box.
        """
        if box_id not in self.monster_boxes:
            self.create_box(box_id, "monster")
        self.monster_boxes[box_id].append(monster)

    def remove_item(self, item: Item) -> None:
        """
        Removes the given item from all boxes.

        Parameters:
            item: The item to remove from all boxes.
        """
        for box in self.item_boxes.values():
            if item in box:
                box.remove(item)
                return

    def remove_monster(self, monster: Monster) -> None:
        """
        Removes the given monster from all boxes.

        Parameters:
            monster: The monster to remove from all boxes.
        """
        for box in self.monster_boxes.values():
            if monster in box:
                box.remove(monster)
                return

    def remove_item_from(self, box_id: str, item: Item) -> None:
        """
        Removes the given item from the box with the given ID.

        Parameters:
            box_id: The ID of the box to remove the item from.
            item: The item to remove from the box.
        """
        if box_id in self.item_boxes:
            self.item_boxes[box_id].remove(item)

    def remove_monster_from(self, box_id: str, monster: Monster) -> None:
        """
        Removes the given monster from the box with the given ID.

        Parameters:
            box_id: The ID of the box to remove the monster from.
            monster: The monster to remove from the box.
        """
        if box_id in self.monster_boxes:
            self.monster_boxes[box_id].remove(monster)

    def get_items_by_iid(self, instance_id: uuid.UUID) -> Optional[Item]:
        """
        Retrieves an item by its instance ID.

        Parameters:
            instance_id: The instance ID of the item to retrieve.

        Returns:
            The item with the given instance ID, or None if not found.
        """
        return next(
            (
                m
                for box in self.item_boxes.values()
                for m in box
                if m.instance_id == instance_id
            ),
            None,
        )

    def get_monsters_by_iid(self, instance_id: uuid.UUID) -> Optional[Monster]:
        """
        Retrieves a monster by its instance ID.

        Parameters:
            instance_id: The instance ID of the monster to retrieve.

        Returns:
            The monster with the given instance ID, or None if not found.
        """
        return next(
            (
                m
                for box in self.monster_boxes.values()
                for m in box
                if m.instance_id == instance_id
            ),
            None,
        )

    def get_items(self, box_id: str) -> list[Item]:
        """
        Retrieves all items in the box with the given ID.

        Parameters:
            box_id: The ID of the box to retrieve items from.

        Returns:
            A list of all items in the box with the given ID.
        """
        return self.item_boxes.get(box_id, [])

    def get_monsters(self, box_id: str) -> list[Monster]:
        """
        Retrieves all monsters in the box with the given ID.

        Parameters:
            box_id: The ID of the box to retrieve monsters from.

        Returns:
            A list of all monsters in the box with the given ID.
        """
        return self.monster_boxes.get(box_id, [])

    def get_box_size(self, box_id: str, box_type: str) -> int:
        """
        Retrieves the size of the box with the given ID and type.

        Parameters:
            box_id: The ID of the box to retrieve the size of.
            box_type: The type of the box to retrieve the size of (either
                "item" or "monster").

        Returns:
            The size of the box with the given ID and type.
        """
        if box_type == "item":
            return len(self.get_items(box_id))
        elif box_type == "monster":
            return len(self.get_monsters(box_id))
        else:
            raise ValueError(f"{box_type} must be 'item' or 'monster'")

    def has_box(self, box_id: str, box_type: str) -> bool:
        """
        Checks if a box with the given ID and type exists.

        Parameters:
            box_id: The ID of the box to check for.
            box_type: The type of the box to check for (either "item"
                or "monster").

        Returns:
            True if the box with the given ID and type exists, False
                otherwise.
        """
        if box_type == "item":
            return box_id in self.item_boxes
        elif box_type == "monster":
            return box_id in self.monster_boxes
        else:
            raise ValueError(f"{box_type} must be 'item' or 'monster'")

    def get_all_items(self) -> list[Item]:
        """
        Retrieves all items in all boxes.

        Returns:
            A list of all items in all boxes.
        """
        return [item for box in self.item_boxes.values() for item in box]

    def get_all_monsters(self) -> list[Monster]:
        """
        Retrieves all monsters in all boxes.

        Returns:
            A list of all monsters in all boxes.
        """
        return [
            monster for box in self.monster_boxes.values() for monster in box
        ]

    def get_all_items_hidden(self) -> list[Item]:
        """
        Retrieves all hidden items in all boxes.

        Returns:
            A list of all hidden items in all boxes.
        """
        return [
            item
            for key, box in self.item_boxes.items()
            if key in HIDDEN_LIST_LOCKER
            for item in box
        ]

    def get_all_monsters_hidden(self) -> list[Monster]:
        """
        Retrieves all hidden monsters in all boxes.

        Returns:
            A list of all hidden monsters in all boxes.
        """
        return [
            monster
            for key, box in self.monster_boxes.items()
            if key in HIDDEN_LIST
            for monster in box
        ]

    def get_all_items_visible(self) -> list[Item]:
        """
        Retrieves all visible items in all boxes.

        Returns:
            A list of all visible items in all boxes.
        """
        return [
            item
            for key, box in self.item_boxes.items()
            if key not in HIDDEN_LIST_LOCKER
            for item in box
        ]

    def get_all_monsters_visible(self) -> list[Monster]:
        """
        Retrieves all visible monsters in all boxes.

        Returns:
            A list of all visible monsters in all boxes.
        """
        return [
            monster
            for key, box in self.monster_boxes.items()
            if key not in HIDDEN_LIST
            for monster in box
        ]

    def move_item(
        self, source_box_id: str, target_box_id: str, item: Item
    ) -> None:
        """
        Moves an item from one box to another.

        Parameters:
            source_box_id: The ID of the box to move the item from.
            target_box_id: The ID of the box to move the item to.
            item: The item to move.
        """
        if (
            source_box_id in self.item_boxes
            and item in self.item_boxes[source_box_id]
        ):
            self.remove_item_from(source_box_id, item)
            self.add_item(target_box_id, item)

    def move_monster(
        self, source_box_id: str, target_box_id: str, monster: Monster
    ) -> None:
        """
        Moves a monster from one box to another.

        Parameters:
            source_box_id: The ID of the box to move the monster from.
            target_box_id: The ID of the box to move the monster to.
            monster: The monster to move.
        """
        if (
            source_box_id in self.monster_boxes
            and monster in self.monster_boxes[source_box_id]
        ):
            self.remove_monster_from(source_box_id, monster)
            self.add_monster(target_box_id, monster)
        else:
            raise ValueError(
                f"{source_box_id} doesn't exist or {monster.slug} isn't in the {source_box_id} box"
            )

    def save(self, state: NPCState) -> None:
        """
        Saves the current state of the box collection.

        Parameters:
            state: The state to save the box collection to.
        """
        state["item_boxes"] = {}
        state["monster_boxes"] = {}
        for box_id, items in self.item_boxes.items():
            state["item_boxes"][box_id] = encode_items(items)
        for box_id, monsters in self.monster_boxes.items():
            state["monster_boxes"][box_id] = encode_monsters(monsters)

    def load(self, save_data: NPCState) -> None:
        """
        Loads the box collection from a saved state.

        Parameters:
            save_data: The saved state to load the box collection from.
        """
        self.item_boxes = {}
        self.monster_boxes = {}
        for box_id, encoded_items in save_data["item_boxes"].items():
            self.item_boxes[box_id] = decode_items(encoded_items)
        for box_id, encoded_monsters in save_data["monster_boxes"].items():
            self.monster_boxes[box_id] = decode_monsters(encoded_monsters)


class ItemBoxes(BoxCollection):
    def __init__(self) -> None:
        """
        Initializes a new ItemBoxes instance.
        """
        super().__init__()

    def save(self, state: NPCState) -> None:
        """
        Saves the current state of the item boxes.

        Parameters:
            state: The state to save the item boxes to.
        """
        super().save(state)

    def load(self, save_data: NPCState) -> None:
        """
        Loads the item boxes from a saved state.

        Parameters:
            save_data: The saved state to load the item boxes from.
        """
        super().load(save_data)


class MonsterBoxes(BoxCollection):
    def __init__(self) -> None:
        """
        Initializes a new MonsterBoxes instance.
        """
        super().__init__()

    def remove_box(self, box_id: str) -> None:
        """
        Removes a monster box with the given ID.

        Parameters:
            box_id: The ID of the box to remove.
        """
        if box_id in self.monster_boxes:
            del self.monster_boxes[box_id]
        else:
            raise ValueError(f"{box_id} doesn't exist.")

    def get_box_ids(self) -> list[str]:
        """
        Retrieves a list of all monster box IDs.

        Returns:
            A list of all monster box IDs.
        """
        return list(self.monster_boxes.keys())

    def get_box_name(self, instance_id: uuid.UUID) -> Optional[str]:
        """
        Retrieves the name of the monster box that contains the monster
        with the given instance ID.

        Parameters:
            instance_id: The instance ID of the monster to find the box for.

        Returns:
            The name of the monster box that contains the monster, or None
            if not found.
        """
        return next(
            (
                box
                for box, monsters in self.monster_boxes.items()
                for m in monsters
                if m.instance_id == instance_id
            ),
            None,
        )

    def is_box_full(
        self, box_id: str, max_capacity: int = prepare.MAX_KENNEL
    ) -> bool:
        """
        Checks if a monster box is full.

        Parameters:
            box_id: The ID of the box to check.
            max_capacity: The maximum capacity of the box (default is
                prepare.MAX_KENNEL).

        Returns:
            True if the box is full, False otherwise.
        """
        return (
            box_id in self.monster_boxes
            and len(self.monster_boxes[box_id]) >= max_capacity
        )

    def merge_boxes(self, source_box_id: str, target_box_id: str) -> None:
        """
        Merges two monster boxes.

        Parameters:
            source_box_id: The ID of the box to merge from.
            target_box_id: The ID of the box to merge to.
        """
        if target_box_id not in self.monster_boxes:
            self.create_box(target_box_id, "monster")
        if source_box_id in self.monster_boxes:
            self.monster_boxes[target_box_id].extend(
                self.monster_boxes[source_box_id]
            )
            del self.monster_boxes[source_box_id]

    def create_and_merge_box(self, box_id: str) -> None:
        """
        Creates a new monster box and merges it with an existing box.

        Parameters:
            box_id: The ID of the box to create and merge.
        """
        i = (
            len(
                [
                    box_id
                    for box_id in self.get_box_ids()
                    if box_id.startswith(box_id)
                    and box_id != box_id
                    and self.is_box_full(box_id)
                ]
            )
            + 1
        )
        new_box_id = f"{box_id}{i}"
        self.create_box(new_box_id, "monster")
        self.merge_boxes(box_id, new_box_id)

    def swap_with_external_monster(
        self, box_id: str, monster_in_box: Monster, external_monster: Monster
    ) -> Monster:
        """
        Swaps a monster in a box with an external monster.

        Parameters:
            box_id: The ID of the box to swap the monster in.
            monster_in_box: The monster in the box to swap.
            external_monster: The external monster to swap with.

        Returns:
            The monster that was swapped out of the box.
        """
        if box_id in self.monster_boxes:
            self.remove_monster_from(box_id, monster_in_box)
            self.add_monster(box_id, external_monster)
            return monster_in_box
        else:
            raise ValueError("Monster not found in box.")

    def swap_with_external_monster_by_iid(
        self, instance_id: uuid.UUID, external_monster: Monster
    ) -> Monster:
        """
        Swaps a monster in a box with an external monster by instance ID.

        Parameters:
            instance_id: The instance ID of the monster to swap.
            external_monster: The external monster to swap with.

        Returns:
            The monster that was swapped out of the box.
        """
        monster = self.get_monsters_by_iid(instance_id)
        box_id = self.get_box_name(instance_id)
        if monster is not None and box_id is not None:
            return self.swap_with_external_monster(
                box_id, monster, external_monster
            )
        else:
            raise ValueError("Monster not found in box.")

    def save(self, state: NPCState) -> None:
        """
        Saves the current state of the monster boxes.

        Parameters:
            state: The state to save the monster boxes to.
        """
        super().save(state)

    def load(self, save_data: NPCState) -> None:
        """
        Loads the monster boxes from a saved state.

        Parameters:
            save_data: The saved state to load the monster boxes from.
        """
        super().load(save_data)
