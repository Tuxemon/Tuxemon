# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon import graphics
from tuxemon.core.asset import get_assets
from tuxemon.core.core_effect import ItemEffectResult
from tuxemon.core.core_processor import (
    ConditionProcessor,
    ConditionValidationResult,
    EffectProcessor,
)
from tuxemon.database.runtime import db
from tuxemon.db import (
    ItemModel,
)
from tuxemon.item.durability import Durability
from tuxemon.item.stock import Stock
from tuxemon.locale.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.monster.stats import BasicStats
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class Item:
    """An item object is an item that can be used either in or out of combat."""

    def __init__(self, slug: str, db_data: ItemModel) -> None:
        self.slug = slug
        self.instance_id: UUID = uuid4()

        self.visuals = db_data.visuals
        self.sound = db_data.sound
        self.sprite = db_data.sprite
        self.category = db_data.category
        self.rarity = db_data.rarity
        self.sort = db_data.sort
        self.cost = db_data.cost
        self.money_multiplier = db_data.money_multiplier
        self.reward_method = db_data.reward_method
        self.behaviors = db_data.behaviors
        self.usable_in = db_data.usable_in
        self.immunity_to_status = db_data.immunity_to_status
        self.menu_actions_data = db_data.menu_actions
        self.granted_techniques = db_data.granted_techniques
        self.granted_statuses = db_data.granted_statuses
        self.break_into_item = db_data.break_into_item
        self.stat_modifiers = db_data.stat_modifiers

        self.core_assets = get_assets()
        self.conditions = self.core_assets.parse_conditions(db_data.conditions)
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_defs = db_data.effects

        self.surface = graphics.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()
        self.dynamic_menu = db_data.dynamic_menu

        self.modifiers = ModifiersHandler(db_data.modifiers)
        self.stock = Stock()
        self.durability = Durability(
            max_wear=db_data.max_wear, break_chance=db_data.break_chance
        )
        self.temporary_stat_boosts = BasicStats()

        self.use_item = T.translate(db_data.use_item)
        self.use_success = T.translate(db_data.use_success)
        self.use_failure = T.translate(db_data.use_failure)
        self.confirm_text = T.translate(db_data.confirm_text)
        self.cancel_text = T.translate(db_data.cancel_text)

    @classmethod
    def create(cls, slug: str) -> Item:
        db_data = ItemModel.lookup(slug, db)
        return cls(slug, db_data)

    @classmethod
    def from_save(cls, save_data: Mapping[str, Any]) -> Item:
        slug = save_data["slug"]
        db_data = ItemModel.lookup(slug, db)

        item = cls(slug, db_data)

        if "quantity" in save_data:
            item.stock.set(save_data["quantity"])
        if "wear" in save_data:
            item.durability.current = save_data["wear"]
        if "instance_id" in save_data:
            item.instance_id = UUID(save_data["instance_id"])

        return item

    @property
    def name(self) -> str:
        return T.translate(self.slug)

    @property
    def description(self) -> str:
        return T.translate(f"{self.slug}_description")

    @property
    def has_wear(self) -> bool:
        return self.durability.has_wear

    @property
    def quantity(self) -> int:
        return self.stock.quantity

    @property
    def wear(self) -> int:
        return self.durability.current

    def is_immune(self, status: str) -> bool:
        return (
            "all" in self.immunity_to_status
            or status in self.immunity_to_status
        )

    def repair(self, amount: int = -1) -> None:
        """Repairs the item if allowed, reducing or resetting its wear level."""
        if not self.behaviors.repairable:
            logger.debug(f"Item {self.slug} is not repairable.")
            return
        self.durability.try_repair(amount)
        logger.debug(
            f"Item {self.slug} repaired. Current wear: {self.durability.current}"
        )

    def set_quantity(self, amount: int = 1) -> None:
        """Set item quantity with clamping at zero, unless it's infinite."""
        self.stock.set(amount)
        logger.debug(f"Item '{self.slug}' quantity set to {self.quantity}")

    def increase_quantity(self, amount: int = 1) -> bool:
        """Increase item quantity unless it's infinite."""
        if not self.stock.try_add(amount):
            logger.warning(
                f"Negative increase: {amount}. Use decrease_quantity instead."
            )
            return False

        logger.debug(f"'{self.slug}' quantity increased to {self.quantity}")
        return True

    def decrease_quantity(self, amount: int = 1) -> bool:
        """Decrease item quantity unless it's infinite, clamping at zero."""
        if not self.stock.try_remove(amount):
            if amount < 0:
                logger.warning(
                    f"Negative decrease: {amount}. Use increase_quantity instead."
                )
            else:
                logger.debug(f"'{self.slug}', but it's already 0.")
            return False

        logger.debug(f"'{self.slug}' quantity decreased to {self.quantity}")
        return True

    def increase_wear(self, amount: int = 1) -> bool:
        """Increase the wear level of the item, clamped to max_wear."""
        just_broke = self.durability.try_increase(amount)
        logger.debug(f"'{self.slug}' wear increased to {self.wear}")
        return just_broke

    def reset_wear(self) -> None:
        """Resets the item's wear level to zero (fully restored)."""
        self.durability.try_reset()
        logger.debug(f"'{self.slug}' wear reset to 0")

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the item has on it's use.
        """
        if self.durability.is_broken:
            logger.debug(f"{self.name} is broken and cannot be used!")
            return False

        if self.stock.quantity == 0:
            return False

        return self.condition_handler.validate_monster(
            session=session, target=target
        ).passed

    def debug_validate_monster(
        self, session: Session, target: Monster
    ) -> ConditionValidationResult:
        """Developer API: returns full structured validation result."""
        return self.condition_handler.validate_monster(
            session=session, target=target
        )

    def use(
        self, session: Session, user: NPC, target: Monster | None
    ) -> ItemEffectResult:
        """
        Applies the item's effects using EffectProcessor and returns the results.
        """
        self.effects = self.core_assets.parse_effects(self.effect_defs)
        self.effect_handler = EffectProcessor(self.effects)
        result = self.effect_handler.process_item(
            session=session, source=self, target=target
        )

        if session.client:
            session.client.active_effect_manager.add_item(self)

        if self.durability.has_wear and self.behaviors.wear_on_use:
            just_broke = self.increase_wear()

            if just_broke:
                logger.warning(f"The item {self.slug} has broken!")

                if self.break_into_item:
                    replacement_slug = self.break_into_item
                    replacement = Item.create(replacement_slug)
                    user.bag.add_item(replacement)
                    logger.debug(f"{self.slug} broke into {replacement_slug}")

                if self.behaviors.destroy_on_break:
                    user.bag.remove_item(self)

        self.consume_if_needed(user, result)
        return result

    def consume_if_needed(self, user: NPC, result: ItemEffectResult) -> None:
        """
        Removes this item from the user's inventory if it's marked consumable,
        and if it's supposed to be consumed based on the result.
        """
        should_consume = (
            CONFIG.items_consumed_on_failure or result.success
        ) and self.behaviors.consumable

        if should_consume:
            self.stock.consume_one()
            if not self.stock.has_any:
                user.bag.remove_item(self)

    def get_state(self) -> Mapping[str, Any]:
        """Prepares a dictionary of the item to be saved."""
        return {
            "slug": self.slug,
            "quantity": self.stock.quantity,
            "wear": self.durability.current,
            "instance_id": self.instance_id.hex,
        }


def decode_items(json_data: Sequence[Mapping[str, Any]] | None) -> list[Item]:
    return [Item.from_save(itm) for itm in (json_data or [])]


def encode_items(itms: Sequence[Item]) -> Sequence[Mapping[str, Any]]:
    return [itm.get_state() for itm in itms]
