# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

from tuxemon.db import EconomyItemModel, EconomyModel, EconomyMonsterModel, db
from tuxemon.item.item import Item
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class Economy:
    """
    Represents an economy in the game, containing items and monsters.
    """

    def __init__(self, slug: Optional[str] = None) -> None:
        if slug:
            self.model = EconomyModel(slug=slug, items=[], monsters=[])
            self.load(slug)

    def load(self, slug: str) -> None:
        """
        Loads the economy from the database based on the given slug.

        Parameters:
            slug: The slug of the economy to load.

        Raises:
            RuntimeError: If the economy with the given slug is not found
            in the database.
        """
        try:
            results = db.lookup(slug, table="economy")
        except KeyError:
            raise RuntimeError(f"Failed to find economy with slug {slug}")

        self.model.slug = results.slug
        self.model.items = [
            EconomyItemModel.model_validate(item) for item in results.items
        ]
        self.model.monsters = [
            EconomyMonsterModel.model_validate(monster)
            for monster in results.monsters
        ]

    def lookup_item_field(self, item_slug: str, field: str) -> Optional[int]:
        """
        Looks up the value of a field for an item in the economy.

        Parameters:
            item_slug: The slug of the item to look up.
            field: The field to look up.

        Returns:
            The value of the field if found, otherwise None.
        """
        item = next(
            (item for item in self.model.items if item.name == item_slug),
            None,
        )
        if item and hasattr(item, field):
            return int(getattr(item, field))
        return None

    def lookup_item(self, item_slug: str, field: str) -> int:
        """
        Looks up the value of a field for an item in the economy, raising an
        error if not found.

        Parameters:
            item_slug: The slug of the item to look up.
            field: The field to look up.

        Returns:
            The value of the field.

        Raises:
            RuntimeError: If the field is not found for the item in the
            economy.
        """
        value = self.lookup_item_field(item_slug, field)
        if value is None:
            raise RuntimeError(
                f"{field.capitalize()} for item '{item_slug}' not found in "
                f"economy '{self.model.slug}'"
            )
        return value

    def lookup_item_price(self, item_slug: str) -> int:
        """
        Looks up the price of an item in the economy.

        Parameters:
            item_slug: The slug of the item to look up.

        Returns:
            The price of the item.
        """
        return self.lookup_item(item_slug, "price")

    def lookup_item_cost(self, item_slug: str) -> int:
        """
        Looks up the cost of an item in the economy.

        Parameters:
            item_slug: The slug of the item to look up.

        Returns:
            The cost of the item.
        """
        return self.lookup_item(item_slug, "cost")

    def lookup_item_inventory(self, item_slug: str) -> int:
        """
        Looks up the inventory of an item in the economy.

        Parameters:
            item_slug: The slug of the item to look up.

        Returns:
            The inventory of the item.
        """
        return self.lookup_item(item_slug, "inventory")

    def update_item_quantity(self, item_slug: str, quantity: int) -> None:
        """
        Updates the quantity of an item in the economy.

        Parameters:
            item_slug: The slug of the item to update.
            quantity: The new quantity of the item.
        """
        self.update_item_field(item_slug, "inventory", quantity)

    def get_item(self, item_slug: str) -> Optional[EconomyItemModel]:
        """
        Gets an item from the economy by its slug.

        Parameters:
            item_slug: The slug of the item to get.

        Returns:
            The item if found, otherwise None.
        """
        return next(
            (item for item in self.model.items if item.name == item_slug),
            None,
        )

    def get_item_field(self, item_slug: str, field: str) -> Optional[int]:
        """
        Gets the value of a field for an item in the economy.

        Parameters:
            item_slug: The slug of the item to get.
            field: The field to get.

        Returns:
            The value of the field if found, otherwise None.
        """
        item = self.get_item(item_slug)
        if item and hasattr(item, field):
            return int(getattr(item, field))
        return None

    def update_item_field(
        self, item_slug: str, field: str, value: int
    ) -> None:
        """
        Updates the value of a field for an item in the economy.

        Parameters:
            item_slug: The slug of the item to update.
            field: The field to update.
            value: The new value of the field.

        Raises:
            RuntimeError: If the item is not found in the economy.
        """
        item = self.get_item(item_slug)
        if item:
            setattr(item, field, value)
        else:
            raise RuntimeError(
                f"Item '{item_slug}' not found in economy '{self.model.slug}'"
            )

    def load_economy_items(self, character: NPC) -> list[Union[Item, Monster]]:
        """
        Loads the items and monsters from the economy for the given character.

        Parameters:
            character: The character to load the items and monsters for.

        Returns:
            The loaded items and monsters.
        """
        entities: list[Union[Item, Monster]] = []
        for item in self.model.items:
            label = f"{self.model.slug}:{item.name}"
            if label not in character.game_variables:
                character.game_variables[label] = self.get_item_field(
                    item.name, "inventory"
                )

            itm_in_shop = Item()
            if item.variables:
                if self.variable(item.variables, character):
                    itm_in_shop.load(item.name)
                    itm_in_shop.quantity = int(character.game_variables[label])
                    entities.append(itm_in_shop)
            else:
                itm_in_shop.load(item.name)
                itm_in_shop.quantity = int(character.game_variables[label])
                entities.append(itm_in_shop)

        for monster in self.model.monsters:
            label = f"{self.model.slug}:{monster.name}"
            if label not in character.game_variables:
                character.game_variables[label] = self.get_monster_field(
                    monster.name, "inventory"
                )

            monster_in_shop = Monster()
            if monster.variables:
                if self.variable(monster.variables, character):
                    monster_in_shop.load_from_db(monster.name)
                    entities.append(monster_in_shop)
            else:
                monster_in_shop.load_from_db(monster.name)
                entities.append(monster_in_shop)

        return entities

    def get_monster_field(
        self, monster_name: str, field: str
    ) -> Optional[int]:
        """
        Gets the value of a field for a monster in the economy.

        Parameters:
            monster_name: The name of the monster to get.
            field: The field to get.

        Returns:
            The value of the field if found, otherwise None.
        """
        monster = next(
            (
                monster
                for monster in self.model.monsters
                if monster.name == monster_name
            ),
            None,
        )
        if monster and hasattr(monster, field):
            return int(getattr(monster, field))
        return None

    def variable(
        self, variables: Sequence[dict[str, str]], character: NPC
    ) -> bool:
        """
        Checks if the given variables match the character's game variables.

        Parameters:
            variables: The variables to check.
            character: The character to check against.

        Returns:
            True if the variables match, otherwise False.
        """
        return all(
            all(
                character.game_variables.get(key) == value
                for key, value in variable.items()
            )
            for variable in variables
        )

    def add_economy_to_npc(
        self, character: NPC, items: list[Union[Monster, Item]]
    ) -> None:
        """
        Adds the given items and monsters to the character's inventory.

        Parameters:
            character: The character to add the items and monsters to.
            items: The items and monsters to add.
        """
        for item in items:
            if isinstance(item, Item):
                character.add_item(item)
            else:
                character.add_monster(item, len(character.monsters))
