# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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


class ItemBoxes:
    """
    A class to manage a collection of item boxes.
    """

    def __init__(self) -> None:
        self.boxes: dict[str, list[Item]] = {}

    def create_box(self, box_id: str) -> None:
        """
        Creates a new item box with the given ID.
        """
        self.boxes[box_id] = []

    def add_item(self, box_id: str, item: Item) -> None:
        """
        Adds an item to a box with the given ID.
        If the box does not exist, it will be created.
        """
        if box_id not in self.boxes:
            self.create_box(box_id)
        self.boxes[box_id].append(item)

    def remove_item(self, item: Item) -> None:
        """
        Removes an item from all boxes.
        """
        for box in self.boxes.values():
            if item in box:
                box.remove(item)
                return

    def remove_item_from(self, box_id: str, item: Item) -> None:
        """
        Removes an item from a box with the given ID.
        """
        if box_id in self.boxes:
            self.boxes[box_id].remove(item)

    def get_items_by_iid(self, instance_id: uuid.UUID) -> Optional[Item]:
        """
        Gets an item by its instance ID.
        """
        return next(
            (
                m
                for box in self.boxes.values()
                for m in box
                if m.instance_id == instance_id
            ),
            None,
        )

    def save(self, state: NPCState) -> None:
        """
        Saves the state of the item boxes.
        """
        state["item_boxes"] = {}
        for box_id, items in self.boxes.items():
            state["item_boxes"][box_id] = encode_items(items)

    def load(self, save_data: NPCState) -> None:
        """
        Loads the state of the item boxes from a saved state.
        """
        self.boxes = {}
        for box_id, encoded_items in save_data["item_boxes"].items():
            self.boxes[box_id] = decode_items(encoded_items)

    def move_item(
        self, source_box_id: str, target_box_id: str, item: Item
    ) -> None:
        """
        Moves an item from one box to another.
        """
        if source_box_id in self.boxes and item in self.boxes[source_box_id]:
            self.remove_item_from(source_box_id, item)
            self.add_item(target_box_id, item)

    def get_items(self, box_id: str) -> list[Item]:
        """
        Gets all items in a box with the given ID.
        """
        return self.boxes.get(box_id, [])

    def get_box_size(self, box_id: str) -> int:
        """
        Gets the number of items in a box with the given ID.
        """
        return len(self.get_items(box_id))

    def has_box(self, box_id: str) -> bool:
        """
        Checks if a box with the given ID exists.
        """
        return box_id in self.boxes

    def get_all_items(self) -> list[Item]:
        """
        Gets all items in all boxes.
        """
        return [item for box in self.boxes.values() for item in box]

    def get_all_items_hidden(self) -> list[Item]:
        """
        Gets all items in hidden boxes.
        """
        return [
            item
            for key, box in self.boxes.items()
            if key in HIDDEN_LIST_LOCKER
            for item in box
        ]

    def get_all_items_visible(self) -> list[Item]:
        """
        Gets all items in visible boxes.
        """
        return [
            item
            for key, box in self.boxes.items()
            if key not in HIDDEN_LIST_LOCKER
            for item in box
        ]


class MonsterBoxes:
    """
    A class to manage a collection of monster boxes.
    """

    def __init__(self) -> None:
        self.boxes: dict[str, list[Monster]] = {}

    def create_box(self, box_id: str) -> None:
        """
        Creates a new monster box with the given ID.
        """
        self.boxes[box_id] = []

    def remove_box(self, box_id: str) -> None:
        """
        Removes a monster box with the given ID.
        """
        if box_id in self.boxes:
            del self.boxes[box_id]

    def add_monster(self, box_id: str, monster: Monster) -> None:
        """
        Adds a monster to a box with the given ID.
        If the box does not exist, it will be created.
        """
        if box_id not in self.boxes:
            self.create_box(box_id)
        self.boxes[box_id].append(monster)

    def remove_monster(self, monster: Monster) -> None:
        """
        Removes a monster from all boxes.
        """
        for box in self.boxes.values():
            if monster in box:
                box.remove(monster)
                return

    def remove_monster_from(self, box_id: str, monster: Monster) -> None:
        """
        Removes a monster from a box with the given ID.
        """
        if box_id in self.boxes:
            self.boxes[box_id].remove(monster)

    def get_monsters_by_iid(self, instance_id: uuid.UUID) -> Optional[Monster]:
        """
        Gets a monster by its instance ID.
        """
        return next(
            (
                m
                for box in self.boxes.values()
                for m in box
                if m.instance_id == instance_id
            ),
            None,
        )

    def get_monsters(self, box_id: str) -> list[Monster]:
        """
        Gets all monsters in a box with the given ID.
        """
        return self.boxes.get(box_id, [])

    def has_box(self, box_id: str) -> bool:
        """
        Checks if a box with the given ID exists.
        """
        return box_id in self.boxes

    def get_box_ids(self) -> list[str]:
        """
        Gets all box IDs.
        """
        return list(self.boxes.keys())

    def get_box_size(self, box_id: str) -> int:
        """
        Gets the number of monsters in a box with the given ID.
        """
        return len(self.get_monsters(box_id))

    def get_box_name(self, instance_id: uuid.UUID) -> Optional[str]:
        """
        Gets the ID of the box that contains a monster with the given instance ID.
        """
        return next(
            (
                box
                for box, monsters in self.boxes.items()
                for m in monsters
                if m.instance_id == instance_id
            ),
            None,
        )

    def get_all_monsters(self) -> list[Monster]:
        """
        Gets all monsters in all boxes.
        """
        return [monster for box in self.boxes.values() for monster in box]

    def get_all_monsters_hidden(self) -> list[Monster]:
        """
        Gets all monsters in hidden boxes.
        """
        return [
            monster
            for key, box in self.boxes.items()
            if key in HIDDEN_LIST
            for monster in box
        ]

    def get_all_monsters_visible(self) -> list[Monster]:
        """
        Gets all monsters in visible boxes.
        """
        return [
            monster
            for key, box in self.boxes.items()
            if key not in HIDDEN_LIST
            for monster in box
        ]

    def is_box_full(
        self, box_id: str, max_capacity: int = prepare.MAX_KENNEL
    ) -> bool:
        """
        Checks if a box is full.
        """
        return box_id in self.boxes and len(self.boxes[box_id]) >= max_capacity

    def move_monster(
        self, source_box_id: str, target_box_id: str, monster: Monster
    ) -> None:
        """
        Moves a monster from one box to another.
        """
        if (
            source_box_id in self.boxes
            and monster in self.boxes[source_box_id]
        ):
            self.remove_monster_from(source_box_id, monster)
            self.add_monster(target_box_id, monster)

    def merge_boxes(self, source_box_id: str, target_box_id: str) -> None:
        """
        Merge the contents of two boxes into a single box.
        """
        if target_box_id not in self.boxes:
            self.create_box(target_box_id)
        if source_box_id in self.boxes:
            self.boxes[target_box_id].extend(self.boxes[source_box_id])
            del self.boxes[source_box_id]

    def create_and_merge_box(self, box_id: str) -> None:
        """
        Moves the content of the given box into a new box with an
        incremented label (e.g., Kennel0 -> Kennel1).
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
        self.create_box(new_box_id)
        self.merge_boxes(box_id, new_box_id)

    def swap_with_external_monster(
        self, box_id: str, monster_in_box: Monster, external_monster: Monster
    ) -> Monster:
        """
        Swaps a monster in a box with an external monster.
        """
        if box_id in self.boxes:
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
        Saves the state of the monster boxes.
        """
        state["monster_boxes"] = {}
        for box_id, monsters in self.boxes.items():
            state["monster_boxes"][box_id] = encode_monsters(monsters)

    def load(self, save_data: NPCState) -> None:
        """
        Loads the state of the monster boxes from a saved state.
        """
        self.boxes = {}
        for box_id, encoded_monsters in save_data["monster_boxes"].items():
            self.boxes[box_id] = decode_monsters(encoded_monsters)
