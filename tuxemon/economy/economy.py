# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.db import EconomyItemModel, EconomyModel, db
from tuxemon.economy.price_policy import PricePolicy
from tuxemon.prepare import GRAD_BLUE

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class Economy:
    """
    Represents an economy's data in the game, containing items and monsters definitions
    with their associated prices, costs, and initial inventory values.
    It provides methods for looking up and updating these definitions.
    """

    def __init__(
        self, slug: Optional[str] = None, policy: Optional[PricePolicy] = None
    ) -> None:
        self.policy = policy or PricePolicy()
        self.model: EconomyModel

        if slug:
            self.load(slug)
        else:
            self.model = EconomyModel(
                slug="",
                resale_multiplier=0.0,
                background=GRAD_BLUE,
                items=[],
                monsters=[],
            )
            logger.warning(
                "Economy initialized without a slug. It's an empty economy."
            )

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
            results = EconomyModel.lookup(slug, db)
            self.model = results
        except Exception as e:
            logger.error(f"Failed to load economy '{slug}': {e}")
            raise RuntimeError(
                f"Economy with slug '{slug}' not found in database."
            ) from e

    def set_policy(self, policy: PricePolicy) -> None:
        self.policy = policy

    def lookup_item_field(self, item_slug: str, field: str) -> Optional[int]:
        """
        Looks up the value of a field for an item definition in the economy.

        Parameters:
            item_slug: The slug of the item definition to look up.
            field: The field to look up (e.g., "price", "cost", "inventory").

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

    def update_item_quantity(self, item_slug: str, quantity: int) -> None:
        """
        Updates the inventory quantity field of an item definition within this economy.
        This primarily affects the data model for the economy itself, not
        an NPC's actual inventory.

        Parameters:
            item_slug: The slug of the item definition to update.
            quantity: The new quantity for the item definition.
        """
        self.update_item_field(item_slug, "inventory", quantity)

    def get_item(self, item_slug: str) -> Optional[EconomyItemModel]:
        """
        Gets an EconomyItemModel definition from the economy by its slug.

        Parameters:
            item_slug: The slug of the item definition to get.

        Returns:
            The EconomyItemModel if found, otherwise None.
        """
        return next(
            (item for item in self.model.items if item.name == item_slug),
            None,
        )

    def update_item_field(
        self, item_slug: str, field: str, value: int
    ) -> None:
        """
        Updates the value of a specific field for an item definition in the economy.

        Parameters:
            item_slug: The slug of the item definition to update.
            field: The field to update.
            value: The new value of the field.

        Raises:
            RuntimeError: If the item definition is not found in the economy.
        """
        item = self.get_item(item_slug)
        if item:
            if hasattr(item, field):
                setattr(item, field, value)
            else:
                raise AttributeError(
                    f"Item definition '{item_slug}' has no field '{field}'"
                )
        else:
            raise RuntimeError(
                f"Item definition '{item_slug}' not found in economy '{self.model.slug}'"
            )

    def get_monster_field(
        self, monster_name: str, field: str
    ) -> Optional[int]:
        """
        Gets the value of a field for a monster definition in the economy.

        Parameters:
            monster_name: The name of the monster definition to get.
            field: The field to get (e.g., "level", "inventory").

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
        Checks if the given variables (conditions from economy data) match
        the character's game variables.

        Parameters:
            variables: A sequence of dictionaries, each representing a set of
                variable-value pairs to check.
            character: The character (NPC or player) whose game variables are
                checked.

        Returns:
            True if all specified variable conditions match the character's
            game variables, otherwise False.
        """
        return all(
            all(
                character.game_variables.get(key) == value
                for key, value in variable.items()
            )
            for variable in variables
        )
