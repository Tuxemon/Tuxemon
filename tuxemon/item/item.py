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
from tuxemon.core.core_effect import ItemEffect, ItemEffectResult
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import ItemCategory, State, db
from tuxemon.locale import T
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "quantity",
)


class Item:
    """An item object is an item that can be used either in or out of combat."""

    effect_manager: Optional[EffectManager] = None
    condition_manager: Optional[ConditionManager] = None

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug = ""
        self.name = ""
        self.description = ""
        self.instance_id = uuid4()
        self.quantity = 1
        self.animation: Optional[str] = None
        self.flip_axes = FlipAxes.NONE
        # The path to the sprite to load.
        self.sprite = ""
        self.category = ItemCategory.none
        self.surface: Optional[Surface] = None
        self.surface_size_original = (0, 0)
        self.combat_state: Optional[CombatState] = None

        self.sort = ""
        self.use_item = ""
        self.use_success = ""
        self.use_failure = ""
        self.usable_in: Sequence[State] = []
        self.cost: int = 0

        if Item.effect_manager is None:
            Item.effect_manager = EffectManager(
                ItemEffect, paths.CORE_EFFECT_PATH.as_posix()
            )
        if Item.condition_manager is None:
            Item.condition_manager = ConditionManager(
                CoreCondition, paths.CORE_CONDITION_PATH.as_posix()
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

    def load(self, slug: str) -> None:
        """Loads and sets this item's attributes from the item.db database.

        The item is looked up in the database by slug.

        Parameters:
            slug: The item slug to look up in the monster.item database.

        """
        try:
            results = db.lookup(slug, table="item")
        except KeyError:
            raise RuntimeError(f"Item {slug} not found")

        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")
        self.quantity = 1
        self.modifiers = results.modifiers

        # item use notifications (translated!)
        self.use_item = T.translate(results.use_item)
        self.use_success = T.translate(results.use_success)
        self.use_failure = T.translate(results.use_failure)

        # misc attributes (not translated!)
        self.world_menu = results.world_menu
        self.behaviors = results.behaviors
        self.cost = results.cost
        self.sort = results.sort
        self.category = results.category or ItemCategory.none
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

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the item has on it's use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def use(
        self, session: Session, user: NPC, target: Optional[Monster]
    ) -> ItemEffectResult:
        """
        Applies the item's effects using EffectProcessor and returns the results.
        """
        result = self.effect_handler.process_item(
            session=session, source=self, target=target
        )

        # If this is a consumable item, remove it from the player's inventory.
        if (
            prepare.CONFIG.items_consumed_on_failure or result.success
        ) and self.behaviors.consumable:
            if self.quantity <= 1:
                user.remove_item(self)
            else:
                self.quantity -= 1

        return result

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the item to be saved to a file.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

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
