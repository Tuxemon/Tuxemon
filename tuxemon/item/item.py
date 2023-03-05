# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
)

import pygame

from tuxemon import graphics, plugin, prepare
from tuxemon.constants import paths
from tuxemon.db import (
    ItemBattleMenu,
    ItemCategory,
    ItemType,
    State,
    db,
    process_targets,
)
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "quantity",
)
INFINITE_ITEMS = 0
# eg 5 capture devices, 1 type and 5 items
MAX_TYPES_BAG = 99


class Item:
    """An item object is an item that can be used either in or out of combat."""

    effects_classes: ClassVar[Mapping[str, Type[ItemEffect[Any]]]] = {}
    conditions_classes: ClassVar[Mapping[str, Type[ItemCondition[Any]]]] = {}

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        if save_data is None:
            save_data = dict()

        self.slug = ""
        self.name = ""
        self.description = ""
        self.instance_id = uuid.uuid4()
        self.quantity = 1
        self.images: Sequence[str] = []
        self.type = ItemType.consumable
        self.sfx = None
        # The path to the sprite to load.
        self.sprite = ""
        self.category = ItemCategory.none
        self.surface: Optional[pygame.surface.Surface] = None
        self.surface_size_original = (0, 0)

        self.effects: Sequence[ItemEffect[Any]] = []
        self.conditions: Sequence[ItemCondition[Any]] = []

        self.sort = ""
        self.use_item = ""
        self.use_success = ""
        self.use_failure = ""
        self.usable_in: Sequence[State] = []
        self.target: Sequence[str] = []
        self.battle_menu: Optional[ItemBattleMenu] = None

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
        """Loads and sets this items's attributes from the item.db database.

        The item is looked up in the database by slug.

        Parameters:
            slug: The item slug to look up in the monster.item database.

        """
        results = db.lookup(slug, table="item")

        if results is None:
            raise RuntimeError(f"item {slug} is not found")

        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")
        self.quantity = 1

        # item use notifications (translated!)
        self.use_item = T.translate(results.use_item)
        self.use_success = T.translate(results.use_success)
        self.use_failure = T.translate(results.use_failure)

        # misc attributes (not translated!)
        self.sort = results.sort
        self.category = results.category or ItemCategory.none
        self.type = results.type or ItemType.consumable
        self.sprite = results.sprite
        self.usable_in = results.usable_in
        self.target = process_targets(results.target)
        self.effects = self.parse_effects(results.effects)
        self.battle_menu = results.battle_menu
        self.conditions = self.parse_conditions(results.conditions)
        self.surface = graphics.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

    def parse_effects(
        self,
        raw: Sequence[str],
    ) -> Sequence[ItemEffect[Any]]:
        """
        Convert effect strings to effect objects.

        Takes raw effects list from the item's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw effects list pulled from the item's db entry.

        Returns:
            Effects turned into a list of ItemEffect objects.

        """
        ret = list()

        for line in raw:
            name = line.split()[0]
            if len(line.split()) > 1:
                params = line.split()[1].split(",")
            else:
                params = []
            try:
                effect = Item.effects_classes[name]
            except KeyError:
                logger.error(f'Error: ItemEffect "{name}" not implemented')
            else:
                ret.append(effect(*params))

        return ret

    def parse_conditions(
        self,
        raw: Sequence[str],
    ) -> Sequence[ItemCondition[Any]]:
        """
        Convert condition strings to condition objects.

        Takes raw condition list from the item's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw conditions list pulled from the item's db entry.

        Returns:
            Conditions turned into a list of ItemCondition objects.

        """
        ret = list()

        for line in raw:
            words = line.split()
            args = "".join(words[1:]).split(",")
            name = words[0]
            params = args[1:]
            try:
                condition = Item.conditions_classes[name]
            except KeyError:
                logger.error(f'Error: ItemCondition "{name}" not implemented')
            else:
                ret.append(condition(*params))

        return ret

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

        result = True

        for condition in self.conditions:
            result = result and condition.test(target)

        return result

    def use(self, user: NPC, target: Monster) -> ItemEffectResult:
        """
        Applies this items's effects as defined in the "effect" column of
        the item database.

        Parameters:
            user: The npc that is using this item.
            target: The monster or object that we are using this item on.

        Returns:
            A dictionary with various effect result properties

        """
        # defaults for the return. items can override these values.
        meta_result: ItemEffectResult = {
            "name": self.name,
            "num_shakes": 0,
            "capture": False,
            "should_tackle": False,
            "success": False,
        }
        # save iid
        user.game_variables["save_item_slug"] = self.slug

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(target)
            meta_result.update(result)

        # If this is a consumable item, remove it from the player's inventory.
        if (
            prepare.CONFIG.items_consumed_on_failure or meta_result["success"]
        ) and self.type == "Consumable":
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
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_items(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> List[Item]:
    return [Item(save_data=itm) for itm in json_data or {}]


def encode_items(itms: Sequence[Item]) -> Sequence[Mapping[str, Any]]:
    return [itm.get_state() for itm in itms]
