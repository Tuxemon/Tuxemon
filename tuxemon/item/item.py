# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from pygame.surface import Surface

from tuxemon import graphics, prepare
from tuxemon.constants import paths
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import ItemCategory, ItemModel, State, db
from tuxemon.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = ("slug", "quantity", "wear")

INFINITE_ITEMS: int = -1


class Item:
    """An item object is an item that can be used either in or out of combat."""

    effect_manager: Optional[EffectManager] = None
    condition_manager: Optional[ConditionManager] = None

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.instance_id: UUID = uuid4()
        self.quantity: int = 1
        self.animation: Optional[str] = None
        self.flip_axes: FlipAxes = FlipAxes.NONE
        self.modifiers: ModifiersHandler = ModifiersHandler()
        # The path to the sprite to load.
        self.sprite: str = ""
        self.category: ItemCategory = ItemCategory.none
        self.surface: Optional[Surface] = None
        self.surface_size_original: tuple[int, int] = (0, 0)
        self.combat_state: Optional[CombatState] = None

        self.sort: str = ""
        self.confirm_text: str = ""
        self.cancel_text: str = ""
        self.use_item: str = ""
        self.use_success: str = ""
        self.use_failure: str = ""
        self.usable_in: Sequence[State] = []
        self.immunity_to_status: Sequence[str] = []
        self.cost: int = 0
        self.wear: int = 0
        self.max_wear: int = 0
        self.break_chance: float = 0.0
        self.menu_actions_data: Sequence[Mapping[str, str]] = []

        if Item.effect_manager is None:
            Item.effect_manager = EffectManager(
                CoreEffect, paths.CORE_EFFECT_PATH, paths.LIBDIR.parent
            )
        if Item.condition_manager is None:
            Item.condition_manager = ConditionManager(
                CoreCondition, paths.CORE_CONDITION_PATH, paths.LIBDIR.parent
            )

        self.effects: Sequence[PluginObject] = []
        self.conditions: Sequence[PluginObject] = []

        self.set_state(save_data)

    @classmethod
    def create(
        cls, slug: str, save_data: Optional[Mapping[str, Any]] = None
    ) -> Item:
        method = cls(save_data)
        method.load(slug)
        return method

    @classmethod
    def test(cls, save_data: Optional[Mapping[str, Any]] = None) -> Item:
        """Creates an Item instance for testing purposes."""
        method = cls(save_data)
        return method

    @property
    def has_wear(self) -> bool:
        return self.max_wear > 0

    @property
    def wear_ratio(self) -> float:
        if self.max_wear == 0:
            return 0.0  # Item doesn’t use wear, no ratio
        return min(max(self.wear / self.max_wear, 0.0), 1.0)

    def load(self, slug: str) -> None:
        """Loads and sets this item's attributes from the item.db database.

        The item is looked up in the database by slug.

        Parameters:
            slug: The item slug to look up in the monster.item database.

        """
        results = ItemModel.lookup(slug, db)
        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")
        self.modifiers = ModifiersHandler(results.modifiers)

        # item use notifications (translated!)
        self.use_item = T.translate(results.use_item)
        self.use_success = T.translate(results.use_success)
        self.use_failure = T.translate(results.use_failure)
        self.confirm_text = T.translate(results.confirm_text)
        self.cancel_text = T.translate(results.cancel_text)

        self.menu_actions_data = results.menu_actions
        self.dynamic_menu = results.dynamic_menu
        self.behaviors = results.behaviors
        self.cost = results.cost
        self.max_wear = results.max_wear
        self.break_chance = results.break_chance
        self.sort = results.sort
        self.immunity_to_status = results.immunity_to_status
        self.category = results.category
        self.sprite = results.sprite
        self.usable_in = results.usable_in
        if self.effect_manager and results.effects:
            self.effects = self.effect_manager.parse_effects(results.effects)
        if self.condition_manager and results.conditions:
            self.conditions = self.condition_manager.parse_conditions(
                results.conditions
            )
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_handler = EffectProcessor(self.effects)
        self.surface = graphics.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

        # Load the animation sprites that will be used for this technique
        self.animation = results.animation
        self.flip_axes = results.flip_axes

    def get_combat_state(self) -> CombatState:
        """Returns the CombatState."""
        if not self.combat_state:
            raise ValueError("No CombatState.")
        return self.combat_state

    def is_immune(self, status: str) -> bool:
        return (
            "all" in self.immunity_to_status
            or status in self.immunity_to_status
        )

    def set_combat_state(self, combat_state: Optional[CombatState]) -> None:
        """Sets the CombatState."""
        self.combat_state = combat_state

    def set_quantity(self, amount: int = 1) -> None:
        """Set item quantity with clamping at zero, unless it's infinite (-1)."""
        if amount < -1:
            logger.warning(f"Invalid quantity: {amount}. Clamping to 0.")
            amount = 0

        self.quantity = amount
        logger.debug(f"Item '{self.slug}' quantity set to {self.quantity}")

    def increase_quantity(self, amount: int = 1) -> bool:
        """Increase item quantity unless it's infinite (-1)."""
        if self.quantity == -1:
            logger.debug(f"'{self.slug}' has infinite quantity.")
            return True

        if amount < 0:
            logger.warning(
                f"Negative increase: {amount}. Use decrease_quantity instead."
            )
            return False

        self.quantity += amount
        logger.debug(f"'{self.slug}' quantity increased to {self.quantity}")
        return True

    def decrease_quantity(self, amount: int = 1) -> bool:
        """Decrease item quantity unless it's infinite (-1), clamping at zero."""
        if self.quantity == -1:
            logger.debug(f"'{self.slug}' has infinite quantity.")
            return True

        if amount < 0:
            logger.warning(
                f"Negative decrease: {amount}. Use increase_quantity instead."
            )
            return False

        if self.quantity == 0:
            logger.debug(f"'{self.slug}', but it's already 0.")
            return False

        self.quantity = max(0, self.quantity - amount)
        logger.debug(f"'{self.slug}' quantity decreased to {self.quantity}")
        return True

    def increase_wear(self, amount: int = 1) -> bool:
        """Increase the wear level of the item, clamped to max_wear."""
        if not self.has_wear or amount < 0:
            logger.warning(
                f"Cannot increase wear: has_wear={self.has_wear}, amount={amount}"
            )
            return False

        self.wear = min(self.wear + amount, self.max_wear)
        logger.debug(f"'{self.slug}' wear increased to {self.wear}")
        return True

    def reset_wear(self) -> None:
        """Resets the item's wear level to zero (fully restored)."""
        if self.has_wear:
            self.wear = 0
            logger.debug(f"'{self.slug}' wear reset to 0")

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the item has on it's use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def execute_item_action(
        self,
        session: Session,
        combat_instance: CombatState,
        user: NPC,
        target: Optional[Monster],
    ) -> ItemEffectResult:
        """Executes the item action and returns the result."""
        self.set_combat_state(combat_instance)
        return self.use(session, user, target)

    def use(
        self, session: Session, user: NPC, target: Optional[Monster]
    ) -> ItemEffectResult:
        """
        Applies the item's effects using EffectProcessor and returns the results.
        """
        result = self.effect_handler.process_item(
            session=session, source=self, target=target
        )
        self.consume_if_needed(user, result)
        return result

    def consume_if_needed(self, user: NPC, result: ItemEffectResult) -> None:
        """
        Removes this item from the user's inventory if it's marked consumable,
        and if it's supposed to be consumed based on the result.
        """
        should_consume = (
            prepare.CONFIG.items_consumed_on_failure or result.success
        ) and self.behaviors.consumable

        if should_consume:
            logger.debug(
                f"Consuming item '{self.slug}' from NPC '{user.slug}'."
            )
            user.items.remove_item(self)
        else:
            logger.debug(
                f"Item '{self.slug}' not consumed (consumable={self.behaviors.consumable}, success={result.success})."
            )

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the item to be saved to a file.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = self.instance_id.hex

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_items(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Item]:
    return [Item(save_data=itm) for itm in json_data or {}]


def encode_items(itms: Sequence[Item]) -> Sequence[Mapping[str, Any]]:
    return [itm.get_state() for itm in itms]
