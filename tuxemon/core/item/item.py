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
# core.item Item handling module.
#
#


import logging
import pprint

from tuxemon.core import prepare, graphics
from tuxemon.core.db import db, process_targets
from tuxemon.core.locale import T

from tuxemon.core import plugin
from tuxemon.constants import paths

logger = logging.getLogger(__name__)


class Item:
    """An item object is an item that can be used either in or out of combat.

    **Example:**

    >>> potion = Item("potion")
    >>> pprint.pprint(potion.__dict__)
    {
        'description': u'Heals a monster by 50 HP.',
        'effects': [u'heal'],
        'slug': 'potion',
        'name': u'potion',
        'sprite': u'resources/gfx/items/potion.png',
        'surface': <Surface(66x90x32 SW)>,
        'surface_size_original': (66, 90),
        'type': u'Consumable'
    }
    """

    effects = dict()
    conditions = dict()

    def __init__(self, session,  user, slug):
        self.session = session
        self.user = user
        self.slug = slug
        self.name = "None"
        self.description = "None"
        self.images = []
        self.type = None
        self.sfx = None
        self.sprite = ""  # The path to the sprite to load.
        self.surface = None  # The pygame.Surface object of the item.
        self.surface_size_original = (0, 0)  # The original size of the image before scaling.

        self.effects = {}
        self.conditions = {}

        self.sort = ""
        self.use_item = ""
        self.use_success = ""
        self.use_failure = ""
        self.usable_in = ""
        self.target = list()

        # load effect and condition plugins if it hasn't been done already
        if not Item.effects:
            Item.effects = plugin.load_plugins(paths.ITEM_EFFECT_PATH, "effects")
            Item.conditions = plugin.load_plugins(paths.ITEM_CONDITION_PATH, "conditions")

        # If a slug of the item was provided, auto-load it from the item database.
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
        >>> potion.load('potion')    # Load an item by slug.
        >>> pprint.pprint(potion.__dict__)
        {
            'description': u'Heals a monster by 50 HP.',
            'effects': [u'heal'],
            'slug': 'potion',
            'name': u'potion',
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
        assert self.sort
        self.type = results["type"]
        self.sprite = results["sprite"]
        self.usable_in = results["usable_in"]
        self.target = process_targets(results["target"])
        self.effects = self.parse_effects(results.get("effects", []))
        self.conditions = self.parse_conditions(results.get("conditions", []))
        self.surface = graphics.load_and_scale(self.sprite)
        self.surface_size_original = self.surface.get_size()

    def parse_effects(self, raw):
        """Takes raw effects list from the item's json and parses it into a form more suitable for the engine.

        :param raw: The raw effects list pulled from the item's db entry.
        :type raw: list

        :rtype: list
        :returns: effects turned into a list of ItemEffect objects
        """

        ret = list()

        for line in raw:
            name = line.split()[0]
            params = line.split()[1].split(",")
            try:
                effect = Item.effects[name]
            except KeyError:
                error = 'Error: ItemEffect "{}" not implemented'.format(name)
                logger.error(error)
            else:
                ret.append(effect(self.session, self.user, params))

        return ret

    def parse_conditions(self, raw):
        """Takes raw condition list from the item's json and parses it into a form more suitable for the engine.

        :param raw: The raw conditions list pulled from the item's db entry.
        :type raw: list

        :rtype: list
        :returns: conditions turned into a list of ItemCondition objects
        """

        ret = list()

        for line in raw:
            words = line.split()
            args = "".join(words[1:]).split(",")
            name = words[0]
            context = args[0]
            params = args[1:]
            try:
                condition = Item.conditions[name]
            except KeyError:
                error = 'Error: ItemCondition "{}" not implemented'.format(name)
                logger.error(error)
            else:
                ret.append(condition(context, self.session, self.user, params))

        return ret

    def advance_round(self):
        """ Advance round for items that take many rounds to use

        * This currently has no use, and may not stay.  It is added
          so that the Item class and Technique class are interchangeable.

        :return: None
        """
        return

    def validate(self, target):
        """Ensures that the target meets all conditions that the
        item has on it's use.

        :param target: The monster or object that we are using this item on.

        :type target: Any

        :rtype: bool
        :returns: whether the item may be used by the user on the target.
        """

        if not self.conditions:
            return True
        if not target:
            return False

        result = True

        for condition in self.conditions:
            result = result and condition.test(target)

        return result

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
        for effect in self.effects:
            result = effect.apply(target)
            meta_result.update(result)

        # If this is a consumable item, remove it from the player's inventory.
        if (prepare.CONFIG.items_consumed_on_failure or meta_result["success"]) and self.type == "Consumable":
            if user.inventory[self.slug]['quantity'] <= 1:
                del user.inventory[self.slug]
            else:
                user.inventory[self.slug]['quantity'] -= 1

        return meta_result


def decode_inventory(session, owner, data):
    """ Reconstruct inventory from save_data

    :param session:
    :param owner:
    :param data: save data
    :type data: Dictionary

    :rtype: Dictionary
    :returns: New inventory
    """
    out = {}
    for slug, quant in (data.get('inventory') or {}).items():
        item = {
            'item': Item(session, owner, slug)
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
