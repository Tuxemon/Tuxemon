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
import logging
import os
import random
from collections import namedtuple

from tuxemon.core import prepare
from tuxemon.core.components import db
from tuxemon.core.components.locale import translator


logger = logging.getLogger(__name__)

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
        self._combat_counter = 0  # number of turns that this technique has been active
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
        self.slug = results["slug"]  # a short English identifier
        self.name = trans(results["name_trans"])  # locale-specific string

        self.sort = results['sort']

        # must be translated before displaying
        self.execute_trans = results['execute_trans']
        self.success_trans = results['success_trans']
        self.failure_trans = results['failure_trans']

        self.category = results["category"]
        self.icon = results["icon"]
        self._combat_counter = 0
        self._life_counter = 0

        if results['types']:
            self.type1 = results["types"][0]
            if len(results['types']) > 1:
                self.type2 = results["types"][1]
            else:
                self.type2 = None
        else:
            self.type1 = self.type2 = None

        self.power = results["power"]
        self.effect = results["effects"]
        self.target = db.process_targets(results["target"])

        # Load the animation sprites that will be used for this technique
        self.animation = results["animation"]
        if self.animation:
            self.images = []
            animation_dir = prepare.BASEDIR + prepare.DATADIR + "/animations/technique/"
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

        :param user: The Monster object that used this technique.
        :param target: Monster object that we are using this technique on.

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
        # TODO: separate classes for each Technique
        # TODO: consider moving message templates to the JSON DB

        # dynamic load for prevent of an infinite load loop ( cf : effect cant use a technique )
        from . import effect as effects
        # defaults for the return. items can override these values in their return.
        meta_result = {
            'name': self.name,
            'success': False,
            'should_tackle': False,
            'capture': False,
        }

        # TODO: handle conflicting values from multiple technique actions
        # TODO: for example, how to handle one saying success, and another not?
        for effect in self.effect:
            last_effect_name = str(effect)
            ndic = {"power":self.power, "technique" : self}
            print(ndic)
            actual_effect = getattr(effects, last_effect_name)(ndic)
            print(actual_effect.param)
            result = actual_effect.execute(user, target)
            meta_result.update(result)

        return meta_result
