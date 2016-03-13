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
#
#
# core.components.item Item handling module.
#
#

import logging
import pprint
import random

from core import tools
from . import db

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

# Load the monster database
items = db.JSONDatabase()
items.load("item")


class Item(object):
    """An item object is an item that can be used either in or out of combat.

    **Example:**

    >>> potion_item = Item("Potion")
    >>> pprint.pprint(potion_item.__dict__)
    {'description': u'Heals a monster by 50 HP.',
     'effect': [u'heal'],
     'id': 1,
     'name': u'Potion',
     'power': 50,
     'sprite': u'resources/gfx/items/potion.png',
     'surface': <Surface(66x90x32 SW)>,
     'surface_size_original': (66, 90),
     'type': u'Consumable'}

    """

    def __init__(self, name=None, id=None):

        self.id = 0
        self.name = "Blank"
        self.description = "None"
        self.effect = []
        self.type = None
        self.power = 0
        self.sprite = ""                    # The path to the sprite to load.
        self.surface = None                 # The pygame.Surface object of the item.
        self.surface_size_original = (0, 0)  # The original size of the image before scaling.

        # If a name of the item was provided, autoload it from the item database.
        if name or id:
            self.load(name, id)

    def load(self, name, id):
        """Loads and sets this items's attributes from the item.db database. The item is looked up
        in the database by name or id.

        :param name: The name of the item to look up in the monster.item database.
        :param id: The id of the item to look up in the item.db database.

        :type name: String
        :type id: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>> potion_item = Item()
        >>> potion_item.load("Potion", None)    # Load an item by name.
        >>> potion_item.load(None, 1)           # Load an item by id.
        >>> pprint.pprint(potion_item.__dict__)
        {'description': u'Heals a monster by 50 HP.',
         'effect': [u'heal'],
         'id': 1,
         'name': u'Potion',
         'power': 50,
         'type': u'Consumable'}

        """

        if name:
            results = items.lookup(name, table="item")
        elif id:
            results = items.lookup_by_id(id, table="item")

        self.name = results["name"]
        self.description = results["description"]
        self.id = results["id"]
        self.type = results["type"]
        self.power = results["power"]
        self.sprite = results["sprite"]
        self.target = results["target"]
        self.usable_in = results["usable_in"]
        self.surface = tools.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

        self.effect = results["effects"]

    def use(self, user, target):
        """Applies this items's effects as defined in the "effect" column of the item database.
        This method will execute a function with the same name as the effect defined in the
        database. If you want to add a new effect, simply create a new function under the Item
        class with the name of the effect you define in item.db.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: bool
        :returns: Success
        """

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effect:
            result = getattr(self, str(effect))(user, target)

        # If this is a consumable item, remove it from the player's inventory.
        if self.type == "Consumable":
            if user.inventory[self.name]['quantity'] <= 1:
                del user.inventory[self.name]
            else:
                user.inventory[self.name]['quantity'] -= 1

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
        >>> potion_item = Item("Potion")
        >>> potion_item.heal(bulbatux, game)
        """

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
        success_max = 0
        damage_modifier = 0
        status_modifier = 0
        item_power = self.power
        random_num = random.randint(0, 1000)

        # Get percent of damage taken and multiply it by 10
        if target.current_hp < target.hp:
            total_damage = target.hp - target.current_hp
            damage_modifier = int((float(total_damage) / target.hp) * 1000)

        # Check if target has any status effects
        if not target.status == "Normal":
            status_modifier = 150

        # Calculate the top of success range (random_num must be in range to succeed)
        success_max = (success_max - (target.level * 10)) + damage_modifier + status_modifier + item_power

        # Debugging Text
        print("--- Capture Variables ---")
        print("(success_max - (target.level * 10)) + damage_modifier + status_modifier + item_power")
        print("(0 - (%s * 10)) + %s + %s + %s = %s" % (
            target.level, damage_modifier, status_modifier, item_power, success_max))
        print("Success if between: 0 -", success_max)
        print("Chance of capture: %s / 100" % (success_max / 10))
        print("Random number:", random_num)

        # If random_num falls between 0 and success_max, capture target
        if 0 <= random_num <= success_max:
            print("It worked!")
            user.add_monster(target)
            return True
        else:
            print("It failed!")
            return False
