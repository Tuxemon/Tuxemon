# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypedDict,
)

import pygame

from tuxemon import graphics, plugin, prepare
from tuxemon.constants import paths
from tuxemon.db import ItemBattleMenu, State, db, process_targets
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.locale import T
from tuxemon.session import Session

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class InventoryItemOptional(TypedDict, total=False):
    infinite: bool


class InventoryItem(InventoryItemOptional):
    item: Item
    quantity: int


class Item:
    """An item object is an item that can be used either in or out of combat."""

    effects_classes: ClassVar[Mapping[str, Type[ItemEffect[Any]]]] = {}
    conditions_classes: ClassVar[Mapping[str, Type[ItemCondition[Any]]]] = {}

    def __init__(
        self,
        session: Session,
        user: NPC,
        slug: str,
    ) -> None:
        self.session = session
        self.user = user
        self.slug = slug
        self.name = "None"
        self.description = "None"
        self.images: Sequence[str] = []
        self.type: Optional[str] = None
        self.sfx = None
        # The path to the sprite to load.
        self.sprite = ""
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

        # Auto-load the item from the item database.
        self.load(slug)

    def load(self, slug: str) -> None:
        """Loads and sets this items's attributes from the item.db database.

        The item is looked up in the database by slug.

        Parameters:
            slug: The item slug to look up in the monster.item database.

        """

        try:
            results = db.lookup(slug, table="item")
        except KeyError:
            logger.error(f"Failed to find item with slug {slug}")
            return

        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        # item use notifications (translated!)
        self.use_item = T.translate(results.use_item)
        self.use_success = T.translate(results.use_success)
        self.use_failure = T.translate(results.use_failure)

        # misc attributes (not translated!)
        self.sort = results.sort
        assert self.sort
        self.type = results.type
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
                params = None
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

    def advance_round(self) -> None:
        """
        Advance round for items that take many rounds to use.

        * This currently has no use, and may not stay.  It is added
          so that the Item class and Technique class are interchangeable.

        """
        return

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

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(target)
            meta_result.update(result)

        # If this is a consumable item, remove it from the player's inventory.
        if (
            prepare.CONFIG.items_consumed_on_failure or meta_result["success"]
        ) and self.type == "Consumable":
            if user.inventory[self.slug]["quantity"] <= 1:
                del user.inventory[self.slug]
            else:
                user.inventory[self.slug]["quantity"] -= 1

        return meta_result


def decode_inventory(
    session: Session,
    owner: NPC,
    data: Mapping[str, Optional[int]],
) -> Dict[str, InventoryItem]:
    """
    Reconstruct inventory from a data dict.

    Parameters:
        session: Game session.
        owner: Inventory owner.
        data: Save data inventory.

    Returns:
        New inventory

    """
    out = {}
    item: InventoryItem
    for slug, quant in data.items():
        item = {
            "item": Item(session, owner, slug),
            "quantity": 1,
        }
        if quant is None:
            # Infinite is used for shopkeepers
            # to ensure they don't run out of an item
            item["infinite"] = True
        else:
            item["quantity"] = quant
        out[slug] = item
    return out


def encode_inventory(
    inventory: Mapping[str, InventoryItem],
) -> Mapping[str, Optional[int]]:
    """
    Construct JSON encodable dict for saving.

    Parameters:
        inventory: the inventory of the player

    Returns:
        Inventory save_data

    """
    return {itm["item"].slug: itm["quantity"] for itm in inventory.values()}
