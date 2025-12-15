# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.db import EconomyItemModel, EconomyModel, EconomyMonsterModel, db
from tuxemon.economy.price_policy import PricePolicy
from tuxemon.item.item import Item
from tuxemon.monster import Monster
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
        self._items_map: dict[str, EconomyItemModel] = {}  # New
        self._monsters_map: dict[str, EconomyMonsterModel] = {}  # New

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
            self._items_map = {item.slug: item for item in self.model.items}
            self._monsters_map = {
                monster.slug: monster for monster in self.model.monsters
            }
        except Exception as e:
            logger.error(f"Failed to load economy '{slug}': {e}")
            raise RuntimeError(
                f"Economy with slug '{slug}' not found in database."
            ) from e

    def set_policy(self, policy: PricePolicy) -> None:
        self.policy = policy

    def get_item(self, item_slug: str) -> Optional[EconomyItemModel]:
        """
        Gets an EconomyItemModel definition from the economy by its slug (O(1) lookup).
        """
        return self._items_map.get(item_slug)

    def get_monster(self, monster_slug: str) -> Optional[EconomyMonsterModel]:
        """
        Gets an EconomyMonsterModel definition from the economy by its name (O(1) lookup).
        """
        return self._monsters_map.get(monster_slug)

    def _get_entity_model(
        self, entity: Item | Monster
    ) -> Optional[EconomyItemModel | EconomyMonsterModel]:
        """
        Internal method to safely retrieve the associated economy model (Item or Monster).
        """
        if isinstance(entity, Item):
            return self.get_item(entity.slug)
        elif isinstance(entity, Monster):
            return self.get_monster(entity.slug)
        return None

    def refresh_maps(self) -> None:
        """
        Rebuild lookup maps from the current model.
        Useful when items/monsters are modified directly.
        """
        self._items_map = {item.slug: item for item in self.model.items}
        self._monsters_map = {
            monster.slug: monster for monster in self.model.monsters
        }

    def update_entity_field(
        self, entity_slug: str, entity_kind: str, field: str, value: int
    ) -> None:
        """
        Updates the value of a specific field for an entity definition in the economy.
        entity_kind should be "item" or "monster".
        """
        entity_model: EconomyItemModel | EconomyMonsterModel | None

        if entity_kind == "item":
            entity_model = self.get_item(entity_slug)
        elif entity_kind == "monster":
            entity_model = self.get_monster(entity_slug)
        else:
            raise ValueError(
                "Invalid entity kind provided. Use 'item' or 'monster'."
            )

        if entity_model is None:
            raise RuntimeError(
                f"Entity definition '{entity_slug}' not found in economy '{self.model.slug}'"
            )

        if hasattr(entity_model, field):
            setattr(entity_model, field, value)
        else:
            raise AttributeError(
                f"Entity definition '{entity_slug}' has no field '{field}'"
            )

    def update_item_quantity(self, item_slug: str, quantity: int) -> None:
        self.update_entity_field(item_slug, "item", "inventory", quantity)

    def update_monster_quantity(
        self, monster_slug: str, quantity: int
    ) -> None:
        self.update_entity_field(
            monster_slug, "monster", "inventory", quantity
        )

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
        if not variables:
            return True
        return all(
            all(
                character.game_variables.get(key) == value
                for key, value in variable.items()
            )
            for variable in variables
        )

    def calculate_price(
        self,
        entity: Item | Monster,
        quantity: int,
        seller_mode: bool = False,
    ) -> tuple[int, int]:
        """
        Calculate the final transaction price for an Item or Monster.

        Parameters:
            entity: The Item or Monster to calculate the price for.
            quantity: The quantity being bought or sold.
            seller_mode: True if the entity is being resold *to* the shop
                (cost for buyer), False if it is being sold *by* the shop
                (price for buyer).

        Returns:
            (final_price, discount_percent)
        """
        entity_model = self._get_entity_model(entity)
        base_value: float

        if seller_mode:
            # --- Calculating Resale Cost (Price to Buyer) ---
            lookup_cost = entity_model.cost if entity_model else None

            if lookup_cost is not None:
                base_value = float(lookup_cost)
            else:
                intrinsic_cost = (
                    entity.cost if isinstance(entity, Item) else entity.hp
                )
                base_value = intrinsic_cost * self.model.resale_multiplier

            return self.policy.apply_resell_modifiers(
                round(base_value), quantity, entity.slug
            )

        else:
            # --- Calculating Purchase Price (Price from Shop) ---
            lookup_price = entity_model.price if entity_model else None

            if lookup_price is not None:
                base_value = lookup_price
            else:
                if isinstance(entity, Item):
                    intrinsic_cost = entity.cost
                    base_value = round(
                        intrinsic_cost * self.model.resale_multiplier
                    )
                    logger.warning(
                        f"Missing price for Item '{entity.slug}'. Falling back to resale calculation."
                    )
                else:
                    raise ValueError(
                        f"Missing mandatory price for monster: {entity.slug} in economy '{self.model.slug}'"
                    )

            return self.policy.apply_modifiers(
                base_value, quantity, entity.slug
            )
