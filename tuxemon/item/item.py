# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import pygame

from tuxemon import graphics, plugin, prepare
from tuxemon.constants import paths
from tuxemon.db import ItemCategory, State, db
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "quantity",
)


class Item:
    """An item object is an item that can be used either in or out of combat."""

    effects_classes: ClassVar[Mapping[str, type[ItemEffect]]] = {}
    conditions_classes: ClassVar[Mapping[str, type[ItemCondition]]] = {}

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug = ""
        self.name = ""
        self.description = ""
        self.instance_id = uuid.uuid4()
        self.quantity = 1
        self.animation: Optional[str] = None
        self.flip_axes = ""
        # The path to the sprite to load.
        self.sprite = ""
        self.category = ItemCategory.none
        self.surface: Optional[pygame.surface.Surface] = None
        self.surface_size_original = (0, 0)

        self.effects: Sequence[ItemEffect] = []
        self.conditions: Sequence[ItemCondition] = []
        self.combat_state: Optional[CombatState] = None

        self.sort = ""
        self.use_item = ""
        self.use_success = ""
        self.use_failure = ""
        self.usable_in: Sequence[State] = []
        self.cost: Optional[int] = None

        # load effect and condition plugins if it hasn't been done already
        if not Item.effects_classes:
            Item.effects_classes = plugin.load_plugins(
                paths.ITEM_EFFECT_PATH,
                "effects",
                interface=ItemEffect,
            )
            Item.conditions_classes = plugin.load_plugins(
                paths.ITEM_CONDITION_PATH,
                "conditions",
                interface=ItemCondition,
            )

        self.set_state(save_data)

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
        self.effects = self.parse_effects(results.effects)
        self.conditions = self.parse_conditions(results.conditions)
        self.surface = graphics.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

        # Load the animation sprites that will be used for this technique
        self.animation = results.animation
        self.flip_axes = results.flip_axes

    def parse_effects(
        self,
        raw: Sequence[str],
    ) -> Sequence[ItemEffect]:
        """
        Convert effect strings to effect objects.

        Takes raw effects list from the item's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw effects list pulled from the item's db entry.

        Returns:
            Effects turned into a list of ItemEffect objects.

        """
        effects = []

        for line in raw:
            parts = line.split(maxsplit=1)
            name = parts[0]
            params = parts[1].split(",") if len(parts) > 1 else []

            try:
                effect_class = Item.effects_classes[name]
            except KeyError:
                logger.error(f'Error: ItemEffect "{name}" not implemented')
            else:
                effects.append(effect_class(*params))

        return effects

    def parse_conditions(
        self,
        raw: Sequence[str],
    ) -> Sequence[ItemCondition]:
        """
        Convert condition strings to condition objects.

        Takes raw condition list from the item's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw conditions list pulled from the item's db entry.

        Returns:
            Conditions turned into a list of ItemCondition objects.

        """
        conditions = []

        for line in raw:
            parts = line.split(maxsplit=2)
            op = parts[0]
            name = parts[1]
            params = parts[2].split(",") if len(parts) > 2 else []

            try:
                condition_class = Item.conditions_classes[name]
            except KeyError:
                logger.error(f'Error: ItemCondition "{name}" not implemented')
                continue

            if op not in ["is", "not"]:
                raise ValueError(f"{op} must be 'is' or 'not'")

            condition = condition_class(*params)
            condition._op = op == "is"
            conditions.append(condition)

        return conditions

    def validate(self, target: Optional[Monster]) -> bool:
        """
        Check if the target meets all conditions that the item has on it's use.

        Parameters:
            target: The monster or object that we are using this item on.

        Returns:
            Whether the item may be used by the user on the target.

        """
        if not self.conditions:
            return True
        if not target:
            return False

        return all(
            (
                condition.test(target)
                if condition._op
                else not condition.test(target)
            )
            for condition in self.conditions
        )

    def use(self, user: NPC, target: Optional[Monster]) -> ItemEffectResult:
        """
        Applies this item's effects as defined in the "effect" column of
        the item database.

        Parameters:
            user: The npc that is using this item.
            target: The monster or object that we are using this item on.

        Returns:
            An ItemEffectResult object containing the result of the item's effect.

        """
        # defaults for the return. items can override these values.
        meta_result = ItemEffectResult(
            name=self.name,
            success=False,
            num_shakes=0,
            extras=[],
        )

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(self, target)
            meta_result.name = result.name
            meta_result.success = meta_result.success or result.success
            meta_result.num_shakes += result.num_shakes
            meta_result.extras.extend(result.extras)

        # If this is a consumable item, remove it from the player's inventory.
        if (
            prepare.CONFIG.items_consumed_on_failure or meta_result.success
        ) and self.behaviors.consumable:
            if self.quantity <= 1:
                user.remove_item(self)
            else:
                self.quantity -= 1

        return meta_result

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
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_items(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Item]:
    return [Item(save_data=itm) for itm in json_data or {}]


def encode_items(itms: Sequence[Item]) -> Sequence[Mapping[str, Any]]:
    return [itm.get_state() for itm in itms]
