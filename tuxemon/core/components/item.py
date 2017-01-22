#!/usr/bin/python
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
#
#
# core.components.item Item handling module.
#
#

import logging
import pprint
import random
from collections import namedtuple

from core import tools
from . import db
from .locale import translator
trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

# Load the monster database
items = db.JSONDatabase()
items.load("item")

class Item(object):
    """An item object is an item that can be used either in or out of combat.

    **Example:**

    >>> potion_item = Item("item_potion")
    >>> pprint.pprint(potion_item.__dict__)
    {'description': u'Heals a monster by 50 HP.',
     'effect': [u'heal'],
     'slug': 'item_potion,
     'name': u'Potion',
     'power': 50,
     'sprite': u'resources/gfx/items/potion.png',
     'surface': <Surface(66x90x32 SW)>,
     'surface_size_original': (66, 90),
     'type': u'Consumable'}

    """

    def __init__(self, slug=None):

        self.slug = slug
        self.name = "Blank"
        self.description = "None"
        self.effect = []
        self.type = None
        self.power = 0
        self.sprite = ""                    # The path to the sprite to load.
        self.surface = None                 # The pygame.Surface object of the item.
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

        >>> potion_item = Item()
        >>> potion_item.load("item_potion")    # Load an item by slug.
        >>> pprint.pprint(potion_item.__dict__)
        {'description': u'Heals a monster by 50 HP.',
         'effect': [u'heal'],
         'slug': 'item_potion',
         'name': u'Potion',
         'power': 50,
         'type': u'Consumable'}

        """

        results = items.lookup(slug, table="item")
        self.slug = results["slug"]                             # short English identifier
        self.name = trans(results["name_trans"])                # will be locale string
        self.description = trans(results["description_trans"])  # will be locale string

        self.type = results["type"]
        self.power = results["power"]
        self.sprite = results["sprite"]
        self.usable_in = results["usable_in"]
        self.surface = tools.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

        #TODO: maybe break out into own function
        from operator import itemgetter
        self.target = map(itemgetter(0), filter(itemgetter(1),
                          sorted(results["target"].items(), key=itemgetter(1), reverse=True)))

        self.effect = results["effects"]

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

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effect:
            last_effect_name = str(effect)
            result = getattr(self, last_effect_name)(user, target)

        # If this is a consumable item, remove it from the player's inventory.
        if result:
            if self.type == "Consumable":
                if user.inventory[self.slug]['quantity'] <= 1:
                    del user.inventory[self.slug]
                else:
                    user.inventory[self.slug]['quantity'] -= 1

        if type(result) == bool:
            result = {"name": last_effect_name, "success": result, "should_tackle": False}
        else:
            result[1]["success"] = result[0]
            result = result[1]
            result["name"] = last_effect_name

        return result

    def heal(self, user, target):
        """This effect heals the target based on the item's power attribute.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: bool
        :returns: Success

        **Examples:**
        >>> potion_item = Item("item_potion")
        >>> potion_item.heal(bulbatux, game)
        """

        if target.current_hp == target.hp:
            return False
         # Heal the target monster by "self.power" number of hitpoints.
        target.current_hp += self.power

        # If we've exceeded the monster's maximum HP, set their health to 100% of their HP.
        if target.current_hp > target.hp:
            target.current_hp = target.hp

        return True

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

        print("--- Capture Variables ---")
        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        catch_check = (3*target.hp - 2*target.current_hp) * target.catch_rate * item_power * status_modifier / (3*target.hp)
        shake_check = 65536 / (255/catch_check)**0.1875

        print("(3*target.hp - 2*target.current_hp) * target.catch_rate * item_power * status_modifier / (3*target.hp)")
        print("(3 * %s - 2 * %s) * %s * %s * %s / (3*%s)" % (
            str(target.hp), str(target.current_hp), str(target.catch_rate), str(item_power), str(status_modifier), str(target.hp)))
        print("65536 / (255/catch_check)**0.1875")
        print("65536 / (255/%s)**0.1875" % str(catch_check))
        print("Each shake has a %s chance of breaking the creature free. (shake_check = %s)" % (str(round((65536-shake_check)/65536, 2)), str(round(shake_check))))

        for i in range(0, 4):
            random_num = random.randint(0, 65536)
            print("shake check %s: random number %s" % (i, random_num))
            if random_num > round(shake_check):
                return False, {"num_shakes": i+1, "should_tackle": False}

        user.add_monster(target)
        return True, {"num_shakes": 4, "should_tackle": False}
