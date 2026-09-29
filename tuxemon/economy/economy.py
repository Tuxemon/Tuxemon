# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.database.runtime import db
from tuxemon.db import EconomyItemModel, EconomyModel, EconomyMonsterModel
from tuxemon.economy.price_policy import PricePolicy
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster
from tuxemon.platform.const.graphics import GRAD_BLUE

logger = logging.getLogger(__name__)


@dataclass
class PriceResult:
    final_price: int
    modifier_percent: int


class Economy:
    """
    Represents an economy's data in the game, containing items and monsters definitions
    with their associated prices, costs, and initial inventory values.
    It provides methods for looking up and updating these definitions.
    """

    def __init__(
        self, slug: str | None = None, policy: PricePolicy | None = None
    ) -> None:
        self.policy = policy or PricePolicy()
        self.model: EconomyModel
        self._items_map: dict[str, EconomyItemModel] = {}
        self._monsters_map: dict[str, EconomyMonsterModel] = {}

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

    def get_item(self, item_slug: str) -> EconomyItemModel | None:
        """
        Gets an EconomyItemModel definition from the economy by its slug (O(1) lookup).
        """
        return self._items_map.get(item_slug)

    def get_monster(self, monster_slug: str) -> EconomyMonsterModel | None:
        """
        Gets an EconomyMonsterModel definition from the economy by its name (O(1) lookup).
        """
        return self._monsters_map.get(monster_slug)

    def refresh_maps(self) -> None:
        """
        Rebuild lookup maps from the current model.
        Useful when items/monsters are modified directly.
        """
        self._items_map = {item.slug: item for item in self.model.items}
        self._monsters_map = {
            monster.slug: monster for monster in self.model.monsters
        }

    def get_model_for(
        self, entity: Item | Monster
    ) -> EconomyItemModel | EconomyMonsterModel | None:
        slug = entity.slug
        if isinstance(entity, Item):
            return self._items_map.get(slug)
        return self._monsters_map.get(slug)

    def _resolve_resale_base(
        self,
        entity: Item | Monster,
        model: EconomyItemModel | EconomyMonsterModel | None,
    ) -> float:
        """
        Determine the base resale value (shop buys from player).
        """
        if model:
            return float(model.cost)

        intrinsic = entity.cost if isinstance(entity, Item) else entity.hp
        return intrinsic * self.model.resale_multiplier

    def _resolve_purchase_base(
        self,
        entity: Item | Monster,
        model: EconomyItemModel | EconomyMonsterModel | None,
    ) -> float:
        """
        Determine the base purchase value (shop sells to player).
        """
        if model:
            return float(model.price)

        if isinstance(entity, Item):
            logger.warning(
                f"Missing price for Item '{entity.slug}'. Falling back to resale calculation."
            )
            return round(entity.cost * self.model.resale_multiplier)

        raise ValueError(
            f"Missing mandatory price for monster: {entity.slug} in economy '{self.model.slug}'"
        )

    def calculate_price(
        self,
        entity: Item | Monster,
        quantity: int,
        seller_mode: bool = False,
    ) -> PriceResult:
        """
        Calculate the final transaction price for an Item or Monster.

        Parameters:
            entity: The Item or Monster to calculate the price for.
            quantity: The quantity being bought or sold.
            seller_mode: True if the entity is being resold *to* the shop
                (cost for buyer), False if it is being sold *by* the shop
                (price for buyer).
        """
        model = self.get_model_for(entity)

        if seller_mode:
            base = self._resolve_resale_base(entity, model)
            final_price, discount = self.policy.apply_resell_modifiers(
                round(base), quantity, entity.slug
            )
            return PriceResult(final_price, discount)

        base = self._resolve_purchase_base(entity, model)
        final_price, discount = self.policy.apply_modifiers(
            round(base), quantity, entity.slug
        )
        return PriceResult(final_price, discount)
