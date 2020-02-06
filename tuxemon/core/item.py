# -*- coding: utf-8 -*-
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
#
#
# core.item Item handling module.
#
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import pprint
import random

from tuxemon.core import tools
from tuxemon.core import prepare
from tuxemon.core.db import db, process_targets
from tuxemon.core.locale import T

logger = logging.getLogger(__name__)


class Item(object):
    """An item object is an item that can be used either in or out of combat.

    **Example:**

    >>> potion = Item("potion")
    >>> pprint.pprint(potion.__dict__)
    {
        'description': u'Heals a monster by 50 HP.',
        'effects': [u'heal'],
        'slug': 'potion',
        'name': u'potion',
        'power': 50,
        'sprite': u'resources/gfx/items/potion.png',
        'surface': <Surface(66x90x32 SW)>,
        'surface_size_original': (66, 90),
        'type': u'Consumable'
    }
    """

    def __init__(self, slug=None):

        self.slug = slug
        self.name = "None"
        self.description = "None"
        self.effect = []
        self.images = []
        self.type = None
        self.power = 0
        self.sprite = ""  # The path to the sprite to load.
        self.surface = None  # The pygame.Surface object of the item.
        self.surface_size_original = (0, 0)  # The original size of the image before scaling.

        # If a slug of the item was provided, autoload it from the item database.
        if slug:
            self.load(slug)

    def load(self, slug):
        """Loads and sets this items's attributes from the item.db database. The item is looked up
        in the database by slug.

        :param slug: The item slug to look up in the monster.item database.

        :type slug: String

        :rtype: None
        :returns: None

        **Examples:**

        >>> potion = Item()
        >>> potion.load("potion")    # Load an item by slug.
        >>> pprint.pprint(potion.__dict__)
        {
            'description': u'Heals a monster by 50 HP.',
            'effects': [u'heal'],
            'slug': 'potion',
            'name': u'potion',
            'power': 50,
            'sprite': u'resources/gfx/items/potion.png',
            'surface': <Surface(66x90x32 SW)>,
            'surface_size_original': (66, 90),
            'type': u'Consumable'
        }
        """

        results = db.lookup(slug, table="item")

        self.slug = results["slug"]                                         # short English identifier
        self.name = T.translate(self.slug)                                  # translated name
        self.description = T.translate("{}_description".format(self.slug))  # will be locale string

        # item use notifications (translated!)
        self.use_item = T.translate(results["use_item"])
        self.use_success = T.translate(results["use_success"])
        self.use_failure = T.translate(results["use_failure"])

        # misc attributes (not translated!)
        self.sort = results['sort']
        self.type = results["type"]
        self.power = results["power"]
        self.sprite = results["sprite"]
        self.usable_in = results["usable_in"]
        self.target = process_targets(results["target"])
        self.effect = results["effects"]
        self.surface = tools.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

    def advance_round(self):
        """ Advance round for items that take many rounds to use

        * This currently has no use, and may not stay.  It is added
          so that the Item class and Technique class are interchangeable.

        :return: None
        """
        return

    def use(self, user, target):
        """Applies this items's effects as defined in the "effect" column of the item database.
        This method will execute a function with the same name as the effect defined in the
        database. If you want to add a new effect, simply create a new function under the Item
        class with the name of the effect you define in item.db.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: dict
        :returns: a dictionary with various effect result properties
        """

        # defaults for the return. items can override these values in their return.
        meta_result = {
            'name': self.name,
            'num_shakes': 0,
            'capture': False,
            'should_tackle': False,
            'success': False
        }

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effect:
            last_effect_name = str(effect)
            result = getattr(self, last_effect_name)(user, target)
            meta_result.update(result)

        # TODO: document how to handle items with multiple effects

        # If this is a consumable item, remove it from the player's inventory.
        if (prepare.CONFIG.items_consumed_on_failure or meta_result["success"]) and self.type == "Consumable":
            if user.inventory[self.slug]['quantity'] <= 1:
                del user.inventory[self.slug]
            else:
                user.inventory[self.slug]['quantity'] -= 1

        return meta_result

    def heal(self, user, target):
        """This effect heals the target based on the item's power attribute.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: bool
        :returns: Success

        **Examples:**
        >>> potion = Item("potion")
        >>> potion.heal(bulbatux, game)
        """

        # TODO: prevent use if the item is not a healing item!
        # TODO: 'user' param is unused - remove or use!

        # don't heal if already at max health
        if target.current_hp == target.hp:
            return {"success": False}

        # Heal the target monster by "self.power" number of hitpoints.
        target.current_hp += self.power

        # If we've exceeded the monster's maximum HP, set their health to 100% of their HP.
        if target.current_hp > target.hp:
            target.current_hp = target.hp

        return {"success": True}

    def capture(self, user, target):
        """Captures target monster.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: bool
        :returns: Success
        """

        # Set up variables for capture equation
        damage_modifier = 0
        status_modifier = 0
        item_power = self.power

        # Get percent of damage taken and multiply it by 10
        if target.current_hp < target.hp:
            total_damage = target.hp - target.current_hp
            damage_modifier = int((float(total_damage) / target.hp) * 1000)

        # Check if target has any status effects
        if not target.status == "Normal":
            status_modifier = 1.5

        # TODO: debug logging this info

        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        catch_check = (3 * target.hp - 2 * target.current_hp) * target.catch_rate * item_power * status_modifier / (
        3 * target.hp)
        shake_check = 65536 / (255 / catch_check) ** 0.1875

        logger.debug("--- Capture Variables ---")
        logger.debug("(3*target.hp - 2*target.current_hp) * target.catch_rate * item_power * status_modifier / (3*target.hp)")

        msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"
        logger.debug(msg.format(target, item_power, status_modifier))

        logger.debug("65536 / (255 / catch_check) ** 0.1875")
        logger.debug("65536 / (255 / {}) ** 0.1875".format(catch_check))

        msg = "Each shake has a {} chance of breaking the creature free. (shake_check = {})"
        logger.debug(msg.format(round((65536 - shake_check) / 65536, 2), round(shake_check)))

        # 4 shakes to give monster change to escape
        for i in range(0, 4):
            random_num = random.randint(0, 65536)
            logger.debug("shake check {}: random number {}".format(i, random_num))
            if random_num > round(shake_check):
                return {"success": False,
                        "capture": True,
                        "num_shakes": i + 1}

        # add creature to the player's monster list
        user.add_monster(target)

        # TODO: remove monster from the other party
        return {"success": True,
                "capture": True,
                "num_shakes": 4}


def decode_inventory(data):
    """ Reconstruct inventory from save_data

    :param data: save data
    :type data: Dictionary

    :rtype: Dictionary
    :returns: New inventory
    """
    out = {}
    for slug, quant in (data.get('inventory') or {}).items():
        item = {
            'item': Item(slug),
        }
        if quant is None:
            item["quantity"] = 1
            # Infinite is used for shopkeepers
            # to ensure they don't run out of an item
            item["infinite"] = True
        else:
            item["quantity"] = quant
        out[slug] = item
    return out


def encode_inventory(inventory):
    """ Construct JSON encodable dict for saving

    :param inventory: the inventory of the player
    :type inventory: Dictionary

    :rtype: Dictionary
    :returns: inventory save_data
    """
    return {
        itm['item'].slug: itm['quantity']
        for itm in inventory.values()
    }
