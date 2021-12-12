#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#
# economy Economy handling module.
#
#

from __future__ import annotations
import logging

from tuxemon import prepare, graphics
from tuxemon.db import db, JSONEconomyItem, JSONEconomy
from tuxemon.locale import T

from tuxemon import plugin
from tuxemon.constants import paths

# from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
# from tuxemon.item.itemcondition import ItemCondition
from tuxemon.session import Session

from typing import (
    Mapping,
    Any,
    Type,
    Optional,
    Sequence,
    Dict,
    TYPE_CHECKING,
    ClassVar,
    TypedDict,
)
import pygame

if TYPE_CHECKING:
    # from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

############ Need to change the below to be about economies, not items...


class EconomyItem(TypedDict):
    item: Item
    price: int
    cost: int


class Economy:
    """An Economy holds a list of item names and their price/cost for this
    economy. They also have a 'parent' economy to look up the price in if item
    isn't found in this economy."""

    def __init__(
        self,
        slug: str,
    ) -> None:
        self.slug = slug

        # Auto-load the economy from the economy database.
        self.load(slug)

    # class Item:
    #     """An item object is an item that can be used either in or out of combat."""
    #
    #     effects_classes: ClassVar[Mapping[str, Type[ItemEffect[Any]]]] = {}
    #     conditions_classes: ClassVar[Mapping[str, Type[ItemCondition[Any]]]] = {}
    #
    #     def __init__(
    #         self,
    #         session: Session,
    #         user: NPC,
    #         slug: str,
    #     ) -> None:
    #         self.session = session
    #         self.user = user
    #         self.slug = slug
    #         self.name = "None"
    #         self.description = "None"
    #         self.images: Sequence[str] = []
    #         self.type: Optional[str] = None
    #         self.sfx = None
    #         self.sprite = ""  # The path to the sprite to load.
    #         self.surface: Optional[pygame.surface.Surface] = None  # The pygame.Surface object of the item.
    #         self.surface_size_original = (0, 0)  # The original size of the image before scaling.
    #
    #         self.effects: Sequence[ItemEffect[Any]] = []
    #         self.conditions: Sequence[ItemCondition[Any]] = []
    #
    #         self.sort = ""
    #         self.use_item = ""
    #         self.use_success = ""
    #         self.use_failure = ""
    #         self.usable_in: Sequence[str] = []
    #         self.target: Sequence[str] = []
    #
    #         # load effect and condition plugins if it hasn't been done already
    #         if not Item.effects_classes:
    #             Item.effects_classes = plugin.load_plugins(
    #                 paths.ITEM_EFFECT_PATH,
    #                 "effects",
    #                 interface=ItemEffect,
    #             )
    #             Item.conditions_classes = plugin.load_plugins(
    #                 paths.ITEM_CONDITION_PATH,
    #                 "conditions",
    #                 interface=ItemCondition,
    #             )
    #
    #         # Auto-load the item from the item database.
    #         self.load(slug)

    #    def load_economy_item(self, item_slug: str, economy_slug: str) -> None:
    #        """Loads and sets this economy item's attributes from the economy.db
    #        database.
    #
    #        The economy item is looked up in the economy database by both the
    #        item slug and the economy slug.
    #        If the item isn't found in the economy, it looks up parent economies
    #        recursively until it finds one, and errors if it doesn't.
    #
    #        Parameters:
    #            item_slug: The item slug to look up in the economy.db database.
    #            economy_slug: The economy slug to look up the item prices for.
    #
    #        """
    #        pass

    def load(self, slug: str) -> None:
        """Loads an economy from the economy.db database.

        The economy is looked up by its slug.

        Parameters:
            slug: The economy slug to look up in the economy.db database.

        """

        try:
            results = db.lookup(slug, table="economy")
        except KeyError:
            logger.error(msg=f"Failed to find economy with slug {slug}")
            return

        self.slug = results["slug"]

        self.parent_slug = results["parent"]
        # self.items: List[JSONEconomyItem] = []  # list of possible technique objects.
        self.items = results["items"]

        ## TODO: The parent tree is a linked list of parent economies,
        # unique for each economy each time it's loaded.
        # Maybe be more efficient in the future (only load each economy once,
        # and share it between each Economy instance), but this is fine for a
        # proof of concept.
        if self.parent_slug:
            self.parent = Economy(self.parent_slug)
        else:
            self.parent = None

    def lookup_item_price(self, item_slug: str) -> int:
        """Looks up the item price from this economy, or any parent economies.

        The item is looked up by its slug.

        Parameters:
            item_slug: The item slug to look up in this, or any parent economy databases.

        Returns:
            Price of item for this or parent economies.
        """

        found_in_economy = False
        for item in self.items:
            if item["item_name"] == item_slug and "price" in item:
                price = item["price"]
                found_in_economy = True

        # If price not in this economy, look up prices in all parents recursively:
        if not found_in_economy:
            if self.parent:
                try:
                    price = self.parent.lookup_item_price(item_slug)
                except RuntimeError as e:
                    raise RuntimeError(
                        f"Price for item '{item_slug}' not "
                        f"found in economy '{self.slug}'"
                    )

            else:
                raise RuntimeError(
                    f"Price for item '{item_slug}' not found in "
                    f"economy '{self.slug}'"
                )

        return price

    def lookup_item_cost(self, item_slug: str) -> int:
        """Looks up the item cost from this economy, or any parent economies.

        The item is looked up by its slug.

        Parameters:
            item_slug: The item slug to look up in this, or any parent economy databases.

        Returns:
            Cost of item for this or parent economies.
        """
        found_in_economy = False
        for item in self.items:
            if item["item_name"] == item_slug and "cost" in item:
                logger.error(f"{item_slug} found in economy {item['cost']}")
                cost = item["cost"]
                found_in_economy = True

        # If cost not in this economy, look up costs in all parents recursively:
        if not found_in_economy:
            if self.parent:
                logger.error("looking in parent {self.parent}")
                try:
                    cost = self.parent.lookup_item_cost(item_slug)
                except RuntimeError as e:
                    raise RuntimeError(
                        f"Cost for item '{item_slug}' not "
                        f"found in economy '{self.slug}'"
                    )

            else:
                raise RuntimeError(
                    f"Cost for item '{item_slug}' not found in "
                    f"economy '{self.slug}'"
                )

        return cost


#     def parse_economy_items(
#         self,
#         raw: Sequence[str],
#     ) -> Sequence[ItemCondition[Any]]:
#         """
#         Convert condition strings to condition objects.
#
#         Takes raw condition list from the item's json and parses it into a
#         form more suitable for the engine.
#
#         Parameters:
#             raw: The raw conditions list pulled from the item's db entry.
#
#         Returns:
#             Conditions turned into a list of ItemCondition objects.
#
#         """
#         ret = list()
#
#         for line in raw:
#             words = line.split()
#             args = "".join(words[1:]).split(",")
#             name = words[0]
#             context = args[0]
#             params = args[1:]
#             try:
#                 condition = Item.conditions_classes[name]
#             except KeyError:
#                 error = f'Error: ItemCondition "{name}" not implemented'
#                 logger.error(error)
#             else:
#                 ret.append(condition(context, self.session, self.user, params))
#
#         return ret


#     def parse_effects(
#         self,
#         raw: Sequence[str],
#     ) -> Sequence[ItemEffect[Any]]:
#         """
#         Convert effect strings to effect objects.
#
#         Takes raw effects list from the item's json and parses it into a
#         form more suitable for the engine.
#
#         Parameters:
#             raw: The raw effects list pulled from the item's db entry.
#
#         Returns:
#             Effects turned into a list of ItemEffect objects.
#
#         """
#         ret = list()
#
#         for line in raw:
#             name = line.split()[0]
#             params = line.split()[1].split(",")
#             try:
#                 effect = Item.effects_classes[name]
#             except KeyError:
#                 error = f'Error: ItemEffect "{name}" not implemented'
#                 logger.error(error)
#             else:
#                 ret.append(effect(self.session, self.user, params))
#
#         return ret

#     def parse_conditions(
#         self,
#         raw: Sequence[str],
#     ) -> Sequence[ItemCondition[Any]]:
#         """
#         Convert condition strings to condition objects.
#
#         Takes raw condition list from the item's json and parses it into a
#         form more suitable for the engine.
#
#         Parameters:
#             raw: The raw conditions list pulled from the item's db entry.
#
#         Returns:
#             Conditions turned into a list of ItemCondition objects.
#
#         """
#         ret = list()
#
#         for line in raw:
#             words = line.split()
#             args = "".join(words[1:]).split(",")
#             name = words[0]
#             context = args[0]
#             params = args[1:]
#             try:
#                 condition = Item.conditions_classes[name]
#             except KeyError:
#                 error = f'Error: ItemCondition "{name}" not implemented'
#                 logger.error(error)
#             else:
#                 ret.append(condition(context, self.session, self.user, params))
#
#         return ret

#     def advance_round(self) -> None:
#         """
#         Advance round for items that take many rounds to use.
#
#         * This currently has no use, and may not stay.  It is added
#           so that the Item class and Technique class are interchangeable.
#
#         """
#         return

#     def validate(self, target: Optional[Monster]) -> bool:
#         """
#         Check if the target meets all conditions that the item has on it's use.
#
#         Parameters:
#             target: The monster or object that we are using this item on.
#
#         Returns:
#             Whether the item may be used by the user on the target.
#
#         """
#         if not self.conditions:
#             return True
#         if not target:
#             return False
#
#         result = True
#
#         for condition in self.conditions:
#             result = result and condition.test(target)
#
#         return result

#     def use(self, user: NPC, target: Monster) -> ItemEffectResult:
#         """
#         Applies this items's effects as defined in the "effect" column of
#         the item database.
#
#         Parameters:
#             user: The npc that is using this item.
#             target: The monster or object that we are using this item on.
#
#         Returns:
#             A dictionary with various effect result properties
#
#         """
#         # defaults for the return. items can override these values.
#         meta_result: ItemEffectResult = {
#             "name": self.name,
#             "num_shakes": 0,
#             "capture": False,
#             "should_tackle": False,
#             "success": False,
#         }
#
#         # Loop through all the effects of this technique and execute the effect's function.
#         for effect in self.effects:
#             result = effect.apply(target)
#             meta_result.update(result)
#
#         # If this is a consumable item, remove it from the player's inventory.
#         if (prepare.CONFIG.items_consumed_on_failure or meta_result["success"]) and self.type == "Consumable":
#             if user.inventory[self.slug]["quantity"] <= 1:
#                 del user.inventory[self.slug]
#             else:
#                 user.inventory[self.slug]["quantity"] -= 1
#
#         return meta_result


#  def decode_inventory(
#      session: Session,
#      owner: NPC,
#      data: Mapping[str, Optional[int]],
#  ) -> Dict[str, InventoryItem]:
#      """
#      Reconstruct inventory from a data dict.
#
#      Parameters:
#          session: Game session.
#          owner: Inventory owner.
#          data: Save data inventory.
#
#      Returns:
#          New inventory
#
#      """
#      out = {}
#      item: InventoryItem
#      for slug, quant in data.items():
#          item = {
#              "item": Item(session, owner, slug),
#              "quantity": 1,
#          }
#          if quant is None:
#              # Infinite is used for shopkeepers
#              # to ensure they don't run out of an item
#              item["infinite"] = True
#          else:
#              item["quantity"] = quant
#          out[slug] = item
#      return out


# def decode_economy(
#     session: Session,
#     owner: NPC,
#     data: Mapping[str, Optional[int]],
# ) -> Dict[str, InventoryItem]:
#     """
#     Reconstruct inventory from a data dict.
#
#     Parameters:
#         session: Game session.
#         owner: Inventory owner.
#         data: Save data inventory.
#
#     Returns:
#         New inventory
#
#     """
#     out = {}
#     item: InventoryItem
#     for slug, quant in data.items():
#         item = {
#             "item": Item(session, owner, slug),
#             "quantity": 1,
#         }
#         if quant is None:
#             # Infinite is used for shopkeepers
#             # to ensure they don't run out of an item
#             item["infinite"] = True
#         else:
#             item["quantity"] = quant
#         out[slug] = item
#     return out
