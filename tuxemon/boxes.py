# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tuxemon.item.item import decode_items, encode_items
from tuxemon.monster.monster import decode_monsters, encode_monsters
from tuxemon.platform.const.sizes import MAX_KENNEL, MAX_LOCKER

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.entity.routing import RoutingPolicy
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.save_system.save_state import NPCState

logger = logging.getLogger(__name__)


@dataclass
class BoxMetadata:
    max_capacity: int
    is_hidden: bool = False


class BoxMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, BoxMetadata]] = {
            "item": {},
            "monster": {},
        }

    def _get_dict(self, box_type: str) -> dict[str, BoxMetadata]:
        if box_type not in self._metadata:
            raise ValueError("Invalid box_type")
        return self._metadata[box_type]

    def create(
        self, box_id: str, box_type: str, metadata: BoxMetadata
    ) -> None:
        metadata_dict = self._get_dict(box_type)
        if box_id in metadata_dict:
            raise ValueError(
                f"{box_type.capitalize()} box '{box_id}' already exists."
            )
        metadata_dict[box_id] = metadata

    def get(self, box_id: str, box_type: str) -> BoxMetadata | None:
        return self._get_dict(box_type).get(box_id)

    def get_all(self, box_type: str) -> dict[str, BoxMetadata]:
        return dict(self._get_dict(box_type))

    def delete(self, box_id: str, box_type: str) -> None:
        metadata_dict = self._get_dict(box_type)
        if box_id not in metadata_dict:
            raise ValueError(
                f"{box_type.capitalize()} box '{box_id}' not found."
            )
        del metadata_dict[box_id]

    def is_hidden(self, box_id: str, box_type: str) -> bool:
        metadata = self.get(box_id, box_type)
        return metadata.is_hidden if metadata else False

    def get_max_capacity(
        self,
        box_id: str,
        box_type: str,
        policy: RoutingPolicy,
        default_capacity: int,
    ) -> int:
        metadata = self.get(box_id, box_type)
        if metadata:
            return max(0, metadata.max_capacity)
        return policy.max_box_capacity or default_capacity

    def set_metadata(
        self, box_type: str, metadata: dict[str, BoxMetadata]
    ) -> None:
        self._metadata[box_type] = metadata


class BoxCollection:
    def __init__(self) -> None:
        """
        Initializes a new BoxCollection instance.
        """
        self.item_boxes: dict[str, list[Item]] = {}
        self.monster_boxes: dict[str, list[Monster]] = {}
        self.metadata_manager = BoxMetadataManager()

    def _get_boxes(self, box_type: str) -> dict[str, list[Any]]:
        if box_type == "item":
            return self.item_boxes
        elif box_type == "monster":
            return self.monster_boxes
        raise ValueError(f"Invalid box_type: {box_type}")

    def _create_box(
        self,
        box_id: str,
        box_type: str,
        default_capacity: int,
        box_metadata: BoxMetadata | None = None,
    ) -> None:
        boxes = self._get_boxes(box_type)
        if box_id in boxes:
            raise ValueError(
                f"{box_type.capitalize()} box '{box_id}' already exists."
            )
        boxes[box_id] = []
        metadata = box_metadata or BoxMetadata(
            max_capacity=default_capacity, is_hidden=False
        )
        self.metadata_manager.create(box_id, box_type, metadata)

    def _remove_box(
        self, box_id: str, box_type: str, force: bool = False
    ) -> None:
        boxes = self._get_boxes(box_type)
        if box_id not in boxes:
            raise ValueError(
                f"{box_type.capitalize()} box '{box_id}' doesn't exist."
            )
        if not force and boxes[box_id]:
            raise ValueError(f"Cannot remove a non-empty {box_type} box.")
        del boxes[box_id]
        self.metadata_manager.delete(box_id, box_type)

    def _merge_and_remove_boxes(
        self,
        source_box_id: str,
        target_box_id: str,
        box_type: str,
        default_capacity: int,
    ) -> None:
        boxes = self._get_boxes(box_type)
        if target_box_id not in boxes:
            self._create_box(target_box_id, box_type, default_capacity)
        if source_box_id in boxes:
            boxes[target_box_id].extend(boxes[source_box_id])
            del boxes[source_box_id]
            source_meta = self.metadata_manager.get(source_box_id, box_type)
            target_meta = self.metadata_manager.get(target_box_id, box_type)
            if source_meta and target_meta:
                target_meta.max_capacity = max(
                    source_meta.max_capacity, target_meta.max_capacity
                )
            if self.metadata_manager.get(source_box_id, box_type) is not None:
                self.metadata_manager.delete(source_box_id, box_type)

    def add_item(self, box_id: str, item: Item) -> None:
        """
        Adds an item to the box with the given ID.

        Parameters:
            box_id: The ID of the box to add the item to.
            item: The item to add to the box.
        """
        if box_id not in self.item_boxes:
            self.item_boxes[box_id] = []
        self.item_boxes[box_id].append(item)

    def add_monster(self, box_id: str, monster: Monster) -> None:
        """
        Adds a monster to the box with the given ID.

        Parameters:
            box_id: The ID of the box to add the monster to.
            monster: The monster to add to the box.
        """
        if box_id not in self.monster_boxes:
            self.monster_boxes[box_id] = []
        self.monster_boxes[box_id].append(monster)

    def set_box_hidden(self, box_id: str, box_type: str, hidden: bool) -> None:
        """
        Toggle the hidden state of a box via its metadata.
        """
        metadata = self.metadata_manager.get(box_id, box_type)
        if metadata is None:
            raise ValueError(
                f"{box_type.capitalize()} box '{box_id}' has no metadata defined."
            )
        metadata.is_hidden = hidden

    def store_party_in_box(
        self,
        box_id: str,
        party: list[Monster],
        max_size: int = MAX_KENNEL,
    ) -> bool:
        """
        Attempts to store all monsters from the given party into the specified box.

        Parameters:
            box_id: The ID of the monster box.
            party: A list of Monster instances to store.
            max_size: The maximum capacity of the box.

        Returns:
            True if the party was successfully stored, False otherwise.
        """
        if box_id not in self.monster_boxes:
            self.monster_boxes[box_id] = []
            self.metadata_manager.create(
                box_id,
                "monster",
                BoxMetadata(max_capacity=max_size, is_hidden=False),
            )

        current_size = len(self.monster_boxes[box_id])
        required_space = len(party)

        if current_size + required_space > max_size:
            logger.error(
                f"Cannot store party in box '{box_id}': "
                f"{required_space} monsters to store, "
                f"but only {max_size - current_size} slots available."
            )
            return False

        self.monster_boxes[box_id].extend(party)
        logger.info(f"Stored {required_space} monsters in box '{box_id}'.")
        return True

    def remove_from_box(
        self, box_type: str, box_id: str | None, obj: Any
    ) -> None:
        boxes = self.item_boxes if box_type == "item" else self.monster_boxes
        if box_id:
            if box_id in boxes and obj in boxes[box_id]:
                boxes[box_id].remove(obj)
        else:
            for box in boxes.values():
                if obj in box:
                    box.remove(obj)
                    return

    def get_items_by_iid(self, instance_id: UUID) -> Item | None:
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

    def get_monsters_by_iid(self, instance_id: UUID) -> Monster | None:
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

    def get_box_ids(self, box_type: str) -> list[str]:
        """Retrieves a list of all box IDs for the given type."""
        if box_type == "item":
            return list(self.item_boxes.keys())
        elif box_type == "monster":
            return list(self.monster_boxes.keys())
        else:
            raise ValueError(f"{box_type} must be 'item' or 'monster'")

    def get_max_capacity(
        self, box_id: str, box_type: str, policy: RoutingPolicy
    ) -> int:
        """
        Retrieve the effective maximum capacity for a box.
        Prefer per-box metadata if available, otherwise fall back to policy or global defaults.
        """
        default = MAX_LOCKER if box_type == "item" else MAX_KENNEL
        return self.metadata_manager.get_max_capacity(
            box_id, box_type, policy, default
        )

    def is_box_full(
        self, box_id: str, box_type: str, policy: RoutingPolicy
    ) -> bool:
        """
        Checks if a box is full, using the capacity defined in its metadata or policy.
        """
        max_capacity = self.get_max_capacity(box_id, box_type, policy)
        if box_type == "item":
            return (
                box_id in self.item_boxes
                and len(self.item_boxes[box_id]) >= max_capacity
            )
        elif box_type == "monster":
            return (
                box_id in self.monster_boxes
                and len(self.monster_boxes[box_id]) >= max_capacity
            )
        else:
            raise ValueError(f"{box_type} must be 'item' or 'monster'")

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

    def is_box_hidden(self, box_id: str, box_type: str) -> bool:
        return self.metadata_manager.is_hidden(box_id, box_type)

    def get_all_by_visibility(self, box_type: str, hidden: bool) -> list[Any]:
        boxes = self.item_boxes if box_type == "item" else self.monster_boxes
        return [
            obj
            for box_id, box in boxes.items()
            if self.is_box_hidden(box_id, box_type) == hidden
            for obj in box
        ]

    def get_all_monsters_visible(self) -> list[Monster]:
        return self.get_all_by_visibility("monster", False)

    def get_all_monsters_hidden(self) -> list[Monster]:
        return self.get_all_by_visibility("monster", True)

    def get_all_items_visible(self) -> list[Item]:
        return self.get_all_by_visibility("item", False)

    def get_all_items_hidden(self) -> list[Item]:
        return self.get_all_by_visibility("item", True)

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
            source_box_id not in self.item_boxes
            or item not in self.item_boxes[source_box_id]
        ):
            raise ValueError(f"Item not found in box '{source_box_id}'.")
        self.remove_from_box("item", source_box_id, item)
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
            self.remove_from_box("monster", source_box_id, monster)
            self.add_monster(target_box_id, monster)
        else:
            raise ValueError(
                f"{source_box_id} doesn't exist or {monster.slug} isn't in the {source_box_id} box"
            )

    def get_state_generic(
        self,
        boxes: dict[str, list[Any]],
        metadata: dict[str, BoxMetadata],
        encoder: Callable[[list[Any]], Sequence[Mapping[str, Any]]],
        label: str,
        metadata_label: str,
    ) -> dict[str, Any]:
        return {
            label: {
                box_id: encoder(contents) for box_id, contents in boxes.items()
            },
            metadata_label: {
                box_id: asdict(meta) for box_id, meta in metadata.items()
            },
        }

    def load_generic(
        self,
        save_data: NPCState,
        label: str,
        metadata_label: str,
        decoder: Callable[[Sequence[Mapping[str, Any]]], list[Any]],
        default_capacity: int,
        owner: NPC | None = None,
    ) -> tuple[dict[str, list[Any]], dict[str, BoxMetadata]]:
        boxes: dict[str, list[Any]] = {}
        metadata: dict[str, BoxMetadata] = {}

        loaded_metadata = getattr(save_data, metadata_label, {}) or {}
        for box_id, metadata_dict in loaded_metadata.items():
            metadata[box_id] = BoxMetadata(**metadata_dict)

        box_data = getattr(save_data, label, {}) or {}
        for box_id, encoded_contents in box_data.items():
            contents = decoder(encoded_contents)
            if box_id not in metadata:
                metadata[box_id] = BoxMetadata(
                    max_capacity=default_capacity, is_hidden=False
                )
            if owner:
                for monster in contents:
                    monster.set_owner(owner)
            boxes[box_id] = contents

        return boxes, metadata


class ItemBoxes(BoxCollection):
    def __init__(self) -> None:
        super().__init__()

    def create_box(
        self, box_id: str, box_metadata: BoxMetadata | None = None
    ) -> None:
        """Create a new item box with optional metadata."""
        super()._create_box(box_id, "item", MAX_LOCKER, box_metadata)

    def remove_box(self, box_id: str, force: bool = False) -> None:
        """Remove an item box, optionally forcing removal if non-empty."""
        super()._remove_box(box_id, "item", force)

    def merge_and_remove_boxes(
        self, source_box_id: str, target_box_id: str
    ) -> None:
        """Merge contents and metadata from one item box into another."""
        super()._merge_and_remove_boxes(
            source_box_id, target_box_id, "item", MAX_LOCKER
        )

    def attempt_add_item(
        self,
        item: Item,
        policy: RoutingPolicy,
        preferred_locker: str | None = None,
    ) -> bool:
        """Attempt to add an item to a box following routing policy and overflow rules."""
        locker = preferred_locker if preferred_locker else policy.get_locker()
        if self.is_box_full(locker, "item", policy):
            logger.warning(
                f"Primary box '{locker}' is full under policy '{policy.name}'."
            )
            overflow_locker = policy.overflow_locker
            if overflow_locker:
                logger.info(
                    f"Attempting to use overflow locker '{overflow_locker}'."
                )
                if overflow_locker not in self.item_boxes:
                    logger.warning(
                        f"Overflow locker '{overflow_locker}' does not exist."
                    )
                    return False
                if not self.is_box_full(overflow_locker, "item", policy):
                    self.add_item(overflow_locker, item)
                    logger.info(
                        f"Item '{item}' added to overflow locker '{overflow_locker}'."
                    )
                    return True
                else:
                    logger.warning(
                        f"Overflow locker '{overflow_locker}' is also full."
                    )
            if policy.locker_name_rules:
                logger.info(
                    f"Creating overflow box using locker_name_rules for base '{locker}'."
                )
                new_box_id = self.create_and_merge_box(
                    locker, policy.locker_name_rules
                )
                self.add_item(new_box_id, item)
                return True
            if policy.auto_discard_if_box_full:
                logger.info(
                    f"Item '{item}' discarded due to full boxes and no overflow options."
                )
                return False
            logger.error(
                f"Item '{item}' could not be stored. All boxes full and no overflow strategy."
            )
            return False
        self.add_item(locker, item)
        logger.info(f"Item '{item}' added to box '{locker}'.")
        return True

    def create_and_merge_box(
        self, box_id: str, locker_name_rules: dict[str, Any]
    ) -> str:
        """Create a new item box using naming rules and merge contents from an existing box."""
        prefix = str(locker_name_rules.get("prefix", ""))
        suffix = str(locker_name_rules.get("suffix", ""))
        i = 1
        while True:
            formatted_suffix = f"{prefix}{i}{suffix}"
            new_box_id = f"{box_id}{formatted_suffix}"
            if new_box_id not in self.get_box_ids("item"):
                break
            i += 1
        self.create_box(new_box_id)
        self.merge_and_remove_boxes(box_id, new_box_id)
        return new_box_id

    def get_state(self) -> dict[str, Any]:
        """Return a serializable state of all item boxes and metadata."""
        return self.get_state_generic(
            self.item_boxes,
            self.metadata_manager.get_all("item"),
            encode_items,
            "item_boxes",
            "item_box_metadata",
        )

    def load(self, save_data: NPCState) -> None:
        """Load item boxes and metadata from saved state."""
        self.item_boxes, item_box_metadata = self.load_generic(
            save_data,
            label="item_boxes",
            metadata_label="item_box_metadata",
            decoder=decode_items,
            default_capacity=MAX_LOCKER,
        )
        self.metadata_manager.set_metadata("item", item_box_metadata)


class MonsterBoxes(BoxCollection):
    def __init__(self) -> None:
        super().__init__()

    def create_box(
        self, box_id: str, box_metadata: BoxMetadata | None = None
    ) -> None:
        """Create a new monster box with optional metadata."""
        super()._create_box(box_id, "monster", MAX_KENNEL, box_metadata)

    def get_total_monster_count(self) -> int:
        """Return the total number of monsters across all boxes."""
        return sum(len(monsters) for monsters in self.monster_boxes.values())

    def find_monster_by_slug_in_boxes(
        self, monster_slug: str
    ) -> tuple[str, Monster] | None:
        """Find a monster by slug and return its box ID and instance."""
        for box_id, monsters in self.monster_boxes.items():
            for monster in monsters:
                if monster.slug == monster_slug:
                    return (box_id, monster)
        return None

    def remove_monsters(self, monsters: list[Monster]) -> None:
        """Remove a list of monsters from any boxes they occupy."""
        for monster in monsters:
            self.remove_from_box("monster", None, monster)

    def remove_box(self, box_id: str, force: bool = False) -> None:
        """Remove a monster box, optionally forcing removal if non-empty."""
        super()._remove_box(box_id, "monster", force)

    def get_box_name(self, instance_id: UUID) -> str | None:
        """Return the box ID containing the monster with the given instance ID."""
        return next(
            (
                box
                for box, monsters in self.monster_boxes.items()
                for m in monsters
                if m.instance_id == instance_id
            ),
            None,
        )

    def merge_and_remove_boxes(
        self, source_box_id: str, target_box_id: str
    ) -> None:
        """Merge contents and metadata from one box into another."""
        super()._merge_and_remove_boxes(
            source_box_id, target_box_id, "monster", MAX_KENNEL
        )

    def create_and_merge_box(
        self, box_id: str, kennel_name_rules: dict[str, Any]
    ) -> str:
        """Create a new box using naming rules and merge contents from an existing box."""
        prefix = str(kennel_name_rules.get("prefix", ""))
        suffix = str(kennel_name_rules.get("suffix", ""))
        i = 1
        while True:
            formatted_suffix = f"{prefix}{i}{suffix}"
            new_box_id = f"{box_id}{formatted_suffix}"
            if new_box_id not in self.get_box_ids("monster"):
                break
            i += 1
        self.create_box(new_box_id)
        self.merge_and_remove_boxes(box_id, new_box_id)
        return new_box_id

    def attempt_add_monster(
        self,
        monster: Monster,
        policy: RoutingPolicy,
        preferred_kennel: str | None = None,
    ) -> bool:
        """Attempt to add a monster to a box following routing policy and overflow rules."""
        kennel = preferred_kennel if preferred_kennel else policy.get_kennel()
        if self.is_box_full(kennel, "monster", policy):
            logger.warning(
                f"Primary box '{kennel}' is full under policy '{policy.name}'."
            )
            overflow_kennel = policy.overflow_kennel
            if overflow_kennel:
                logger.info(
                    f"Attempting to use overflow kennel '{overflow_kennel}'."
                )
                if overflow_kennel not in self.monster_boxes:
                    logger.warning(
                        f"Overflow kennel '{overflow_kennel}' does not exist."
                    )
                    return False
                if not self.is_box_full(overflow_kennel, "monster", policy):
                    self.add_monster(overflow_kennel, monster)
                    logger.info(
                        f"Monster '{monster}' added to overflow kennel '{overflow_kennel}'."
                    )
                    return True
                else:
                    logger.warning(
                        f"Overflow kennel '{overflow_kennel}' is also full."
                    )
            if policy.kennel_name_rules:
                logger.info(
                    f"Creating overflow box using kennel_name_rules for base '{kennel}'."
                )
                new_box_id = self.create_and_merge_box(
                    kennel, policy.kennel_name_rules
                )
                self.add_monster(new_box_id, monster)
                return True
            if policy.auto_release_if_box_full:
                logger.info(
                    f"Monster '{monster}' discarded due to full boxes and no overflow options."
                )
                return False
            logger.error(
                f"Monster '{monster}' could not be stored. All boxes full and no overflow strategy."
            )
            return False
        self.add_monster(kennel, monster)
        logger.info(f"Monster '{monster}' added to box '{kennel}'.")
        return True

    def swap_with_external_monster(
        self, box_id: str, monster_in_box: Monster, external_monster: Monster
    ) -> Monster:
        """Swap a monster in a box with an external monster."""
        if box_id not in self.monster_boxes:
            raise ValueError(f"Box '{box_id}' not found.")
        box_contents = self.monster_boxes[box_id]
        if monster_in_box not in box_contents:
            raise ValueError(f"Monster not found in box '{box_id}'.")
        self.remove_from_box("monster", box_id, monster_in_box)
        self.add_monster(box_id, external_monster)
        return monster_in_box

    def swap_with_external_monster_by_iid(
        self, instance_id: UUID, external_monster: Monster
    ) -> Monster:
        """Swap a monster by instance ID with an external monster."""
        for box_id, monsters in self.monster_boxes.items():
            for monster in monsters:
                if monster.instance_id == instance_id:
                    return self.swap_with_external_monster(
                        box_id, monster, external_monster
                    )
        raise ValueError("Monster not found in box.")

    def get_state(self) -> dict[str, Any]:
        """Return a serializable state of all monster boxes and metadata."""
        return self.get_state_generic(
            self.monster_boxes,
            self.metadata_manager.get_all("monster"),
            encode_monsters,
            "monster_boxes",
            "monster_box_metadata",
        )

    def load(self, char: NPC, save_data: NPCState) -> None:
        """Load monster boxes and metadata from saved state, assigning ownership to a character."""
        self.monster_boxes, monster_box_metadata = self.load_generic(
            save_data,
            label="monster_boxes",
            metadata_label="monster_box_metadata",
            decoder=decode_monsters,
            default_capacity=MAX_KENNEL,
            owner=char,
        )
        self.metadata_manager.set_metadata("monster", monster_box_metadata)
