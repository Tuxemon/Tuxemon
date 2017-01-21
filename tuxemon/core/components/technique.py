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
#
#
import os
import random
from collections import namedtuple

from core import prepare, tools
from core.components import db
from core.components.locale import translator
trans = translator.translate


# Load the technique database
techniques = db.JSONDatabase()
techniques.load("technique")

tech_ret_value = namedtuple("use", "name success properties")

class Technique(object):
    """A technique object is a particular skill that tuxemon monsters can use
    in battle.

    **Example:**

    >>> poison_tech = Technique("technique_poison_sting")
    >>> pprint.pprint(poison_tech.__dict__)
        {'category': u'special',
         'effect': [u'poison', u'damage'],
         'name': u'Poison Sting',
         'power': 40,
         'tech_id': 2,
         'type1': u'Poison',
         'type2': None}

    """

    def __init__(self, slug=None):
        self.slug = slug
        self.name = "Pound"
        self.category = "attack"
        self.type1 = "Normal"
        self.type2 = None
        self._combat_counter = 0     # number of turns that this technique has been active
        self.power = 1
        self.effect = []

        # If a slug of the technique was provided, autoload it.
        if slug:
            self.load(slug)

    def load(self, slug):
        """Loads and sets this technique's attributes from the technique
        database. The technique is looked up in the database by slug.

        :param slug: The slug of the technique to look up in the database.

        :type slug: String

        :rtype: None
        :returns: None

        **Examples:**

        >>>

        """

        results = techniques.lookup(slug, table="technique")
        self.slug = results["slug"]
        self.name = trans(results["name_trans"])
        self.category = results["category"]
        self.icon = results["icon"]

        self._combat_counter = 0
        self._life_counter = 0

        self.type1 = results["types"][0]
        if len(results['types']) > 1:
            self.type2 = results["types"][1]
        else:
            self.type2 = None

        self.power = results["power"]
        self.effect = results["effects"]

        #TODO: maybe break out into own function
        from operator import itemgetter
        self.target = map(itemgetter(0), filter(itemgetter(1),
                          sorted(results["target"].items(), key=itemgetter(1), reverse=True)))

        # Load the animation sprites that will be used for this technique
        self.animation = results["animation"]
        self.images = []
        animation_dir = prepare.BASEDIR + "resources/animations/technique/"
        directory = sorted(os.listdir(animation_dir))
        for image in directory:
            if self.animation and image.startswith(self.animation):
                self.images.append("animations/technique/" + image)

        # Load the sound effect for this technique
        sfx_directory = "sounds/technique/"
        self.sfx = sfx_directory + results["sfx"]

    def advance_round(self, number=1):
        """ Advance the turn counters for this technique

        Techniques have two counters currently, a "combat counter" and a "life counter".
        Combat counters should be reset with combat begins.
        Life counters will be set to zero when the Technique is created, but will never
        be reset.

        Calling this function will advance both counters

        :return: None
        """
        self._combat_counter += 1
        self._life_counter += 1

    def reset_combat_counter(self):
        """ Reset the combat counter.
        """
        self._combat_counter = 0

    def use(self, user, target):
        """Applies this technique's effects as defined in the "effect" column of the technique
        database. This method will execute a function with the same name as the effect defined in
        the database. If you want to add a new effect, simply create a new function under the
        Technique class with the name of the effect you define in monster.db.

        :param user: The core.components.monster.Monster object that used this technique.
        :param target: The core.components.monter.Monster object that we are using this
            technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: dictionary
        :returns: a dictionary with the effect name, success and misc properties

        **Examples:**

        >>> poison_tech = Technique("technique_poison_sting")
        >>> bulbatux.learn(poison_tech)
        >>>
        >>> bulbatux.moves[0].use(user=bulbatux, target=tuxmander)
        """
        # Loop through all the effects of this technique and execute the effect's function.
        # TODO: more robust API

        # 'result' can either be a tuple or a boolean.
        result = None
        last_effect_name = None
        for effect in self.effect:
            last_effect_name = str(effect)
            result = getattr(self, last_effect_name)(user, target)

        if type(result) is bool:
            return {"name": last_effect_name, "success": result, "should_tackle": result}

        result[1]["success"] = result[0]
        result = result[1]
        result["name"] = last_effect_name
        return result

    def calculate_damage(self, user, target):
        # Original Pokemon battle damage formula:
        # according to: http://www.math.miami.edu/~jam/azure/compendium/battdam.htm
        # ((2 * user.level / 7) * user.attack * self.power) / target.defense) / 50) +2) * stab_bonus) * type_modifiers/10) * random.randrange(217, 255))/255

        if self.category == "physical":
            level_modifier = ((2 * user.level) / 7.)
            attack_modifier = user.attack * self.power
            return int(((level_modifier * attack_modifier) / float(target.defense)) / 50.)

        elif self.category == "special":
            level_modifier = ((2 * user.level) / 7.)
            attack_modifier = user.special_attack * self.power
            return int(((level_modifier * attack_modifier) / float(target.special_defense)) / 50.)

        elif self.category == "poison":
            return int(self.power)

        return 0

    def damage(self, user, target):
        """This effect applies damage to a target monster. Damage calculations are based upon the
        original Pokemon battle damage formula. This effect will be applied if "damage" is defined
        in this technique's effect list.

        :param user: The core.components.monster.Monster object that used this technique.
        :param target: The core.components.monster.Monster object that we are using this
            technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: bool
        """
        damage = self.calculate_damage(user, target)
        if damage:
            target.current_hp -= damage
            return True
        return False

    def poison(self, user, target):
        """This effect has a chance to apply the poison status effect to a target monster.
        Currently there is a 1/10 chance of poison.

        :param user: The core.components.monster.Monster object that used this technique.
        :param target: The core.components.monster.Monster object that we are using this
            technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: bool
        """
        already_poisoned = any(t for t in target.status if t.slug == "status_poison")

        if not already_poisoned and random.randrange(1, 2) == 1:
            target.apply_status(Technique("status_poison"))
            return True

        return False

    def faint(self, user, target):
        """ Faint this monster.  Typically, called by combat to faint self, not others.

        :param user: The core.components.monster.Monster object that used this technique.
        :param target: The core.components.monster.Monster object that we are using this
            technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: bool
        """
        already_fainted = any(t for t in target.status if t.name == "status_faint")

        if already_fainted:
            raise RuntimeError
        else:
            target.apply_status(Technique("status_faint"))
            return True

    def swap(self, user, target):
        """ Used just for combat: change order of monsters

        Position of monster in party will be changed

        :param user: core.components.monster.Monster
        :param target: core.components.monster.Monster
        :returns: None
        """
        # TODO: relies on setting "other" attribute.  maybe clear it up later
        index = user.monsters.index(self.other)
        user.monsters[index] = target
        user.monsters[0] = self.other
        return True
