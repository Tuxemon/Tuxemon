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
# core.components.monster Tuxemon monster module
#
#
import logging
import pprint
import random

from core import tools
from core.components import ai
from core.components.technique import Technique
from . import db
from . import fusion

from .locale import translator
trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

# Load the monster database
monsters = db.JSONDatabase()
monsters.load("monster")
monsters.load("technique")


# class definition for first active tuxemon to use in combat:
class Monster(object):
    """A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.

    :param: None

    **Example:**

    >>> bulbatux = Monster()
    >>> bulbatux.load_from_db("Bulbatux")
    >>> pprint.pprint(bulbatux.__dict__)
        {'attack': 10,
         'attack_modifier': [u'1', u'1.1', u'1.2'],
         'body': <core.components.fusion.Body instance at 0x1607638>,
         'defense': u'1,1.1,1.2',
         'defense_modifier': [u'1', u'1.1', u'1.2'],
         'hp': 30,
         'hp_modifier': [u'0.9', u'1', u'1.1'],
         'level': 0,
         'moves': [<__main__.Technique instance at 0x160b4d0>],
         'name': u'Bulbatux',
         'special_attack': 9,
         'special_attack_modifier': [u'1', u'1.1', u'1.2'],
         'special_defense': 8,
         'special_defense_modifier': [u'1', u'1.1', u'1.2'],
         'speed': 7,
         'speed_modifier': [u'1', u'1.1', u'1.2'],
         'status': 'Normal',
         'type1': u'grass',
         'type2': u'poison',
         'experience_give_modifier': 3,
         'experience_required_modifier': 55}

    """

    def __init__(self):
        self.slug = ""
        self.name = ""          # The display name of the Tuxemon
        self.description = ""
        self.level = 0
        self.hp = 0
        self.current_hp = 0
        self.attack = 0
        self.defense = 0
        self.speed = 0
        self.special_attack = 0
        self.special_defense = 0
        self.moves = []         # A list of technique objects. Used in combat.
        self.moveset = []       # A list of possible technique objects.
        self.ai = None

        self.hp_modifier = [0, 0, 0]
        self.attack_modifier = [0, 0, 0]
        self.defense_modifier = [0, 0, 0]
        self.speed_modifier = [0, 0, 0]
        self.special_attack_modifier = [0, 0, 0]
        self.special_defense_modifier = [0, 0, 0]
        self.experience_give_modifier = 0
        self.experience_required_modifier = 0
        self.total_experience = 0

        self.type1 = "Normal"
        self.type2 = None

        self.status = list()
        self.status_damage = 0
        self.status_turn = 0

        self.weight = 0

		# the multiplier for checks when a monster ball is thrown.
        self.catch_rate = 1;

        # The tuxemon's state is used for various animations, etc. For example
        # a tuxemon's state might be "attacking" or "fainting" so we know when
        # to play the animations for those states.
        self.state = ""

        # A fusion body object that contains the monster's face and body
        # sprites, as well as _color scheme.
        self.body = fusion.Body()

        # Set up our sprites.
        self.sprites = {}
        self.front_battle_sprite = ""
        self.back_battle_sprite = ""
        self.menu_sprite = ""

    def load_from_db(self, slug):
        """Loads and sets this monster's attributes from the monster.db database.
        The monster is looked up in the database by name.

        :param name: The name of the monster to look up in the monster database.
        :type name: String

        :rtype: None
        :returns: None

        **Examples:**

        >>> bulbatux = Monster()
        >>> bulbatux.load_from_db("Bigfin")

        """

        # Look up the monster by name and set the attributes in this instance
        results = monsters.lookup(slug)

        if results is None:
            print("monster {} is not found".format(slug))
            raise RuntimeError

        self.slug = results["slug"]                             # short English identifier
        self.name = trans(results["name_trans"])                # will be locale string
        self.description = trans(results["description_trans"])  # will be locale string

        self.hp = results["hp_base"]
        self.current_hp = results["hp_base"]
        self.attack = results["attack_base"]
        self.defense = results["defense_base"]
        self.speed = results["speed_base"]
        self.special_attack = results["special_attack_base"]
        self.special_defense = results["special_defense_base"]

        self.hp_modifier = (
            results["hp_mod"] - 1,
            results["hp_mod"],
            results["hp_mod"] + 1
        )
        self.attack_modifier = (
            results["attack_mod"] - 1,
            results["attack_mod"],
            results["attack_mod"] + 1
        )
        self.defense_modifier = (
            results["defense_mod"] - 1,
            results["defense_mod"],
            results["defense_mod"] + 1,
        )
        self.speed_modifier = (
            results["speed_mod"] - 1,
            results["speed_mod"],
            results["speed_mod"] + 1,
        )
        self.special_attack_modifier = (
            results["special_attack_mod"] - 1,
            results["special_attack_mod"],
            results["special_attack_mod"] + 1,
        )
        self.special_defense_modifier = (
            results["special_defense_mod"] - 1,
            results["special_defense_mod"],
            results["special_defense_mod"] + 1,
        )
        self.experience_give_modifier = results["exp_give_mod"]
        self.experience_required_modifier = results["exp_req_mod"]

        self.type1 = results["types"][0]
        if len(results["types"]) > 1:
            self.type2 = results["types"][1]
        else:
            self.type2 = None

        self.weight = results['weight']

        # Look up the moves that this monster can learn AND LEARN THEM.
        for move in results["moveset"]:
            self.moveset.append(move)
            if move['level_learned'] >= self.level:
                technique = Technique(move['technique'])
                self.learn(technique)

        # Look up the monster's sprite image paths
        self.front_battle_sprite = results['sprites']['battle1']
        self.back_battle_sprite = results['sprites']['battle2']
        self.menu_sprite = results['sprites']['menu1']

        # Load the monster AI
        # TODO: clean up AI 'core' loading and what not
        ai_result = results['ai']
        if ai_result == "SimpleAI":
            self.ai = ai.SimpleAI()
        elif ai_result == "RandomAI":
            self.ai = ai.RandomAI()


    def load_sprite_from_db(self):
        """Looks up the path to the monster's battle sprites so they can be
        loaded as pygame surfaces.

        :param: None

        :rtype: None
        :returns: None

        """

        # Look up the monster's sprite image paths
        results = monsters.lookup_sprite(self.slug)

        self.front_battle_sprite = results["sprite_battle1"]
        self.back_battle_sprite = results["sprite_battle2"]
        self.menu_sprite = results["sprite_menu1"]

    def learn(self, technique):
        """Adds a technique to this tuxemon's moveset.

        :param technique: The core.components.monster.Technique object for
            the monster to learn.

        :type technique: core.components.monster.Technique

        :rtype: None
        :returns: None

        **Examples:**

        >>> bulbatux.learn(Technique())
        >>> bulbatux.moves[0].use(bulbatux, target=tuxmander)

        """

        self.moves.append(technique)

    def give_experience(self, amount=1):
        """Gives the Monster a specified amount of experience, and levels
        up the monster if necessary.

        :param amount: The amount of experience to add to the monster.

        :type amount: Integer

        :rtype: None
        :returns: None

        **Example:**

        >>> bulbatux.give_experience(20)
        """
        self.total_experience += amount
        if self.total_experience >= (self.experience_required_modifier * (self.level + 1) ** 3):
            #Level up worthy monsters
            self.level_up()

    def apply_status(self, status):
        """ Apply a status to the monster

        :type status: core.components.technique.Technique
        :rtype: None
        """
        self.status.append(status)

    def set_stats(self):
        """Sets the monsters initial stats, or imporves stats
        when called during a level up. If this is being called
        when the game is creating a monster, it should be looped
        through. Once for each level of the monster being created.

        :rtype: None
        :returns: None

        **Example:**


        """
        if self.level < 10:
            level = 10
        else:
            level = self.level

        hp_up = int(self.hp * 0.1 + random.choice(self.hp_modifier) * (level / 10))
        self.current_hp += hp_up
        self.hp += hp_up

        self.attack += int(
            self.attack * 0.1 + random.choice(self.attack_modifier) * (level / 10))
        self.defense += int(
            self.defense * 0.1 + random.choice(self.defense_modifier) * (level / 10))
        self.speed += int(
            self.speed * 0.1 + random.choice(self.speed_modifier) * (level / 10))
        self.special_attack += int(
            self.special_attack * 0.1 + random.choice(self.special_attack_modifier) * (level / 10))
        self.special_defense += int(
            self.special_defense * 0.1 + random.choice(self.special_defense_modifier) * (level / 10))

        # Display stats each time they are calculated
        """print("---- Level: %s ----" % self.level)
        print("HP:", self.hp)
        print("Attack:", self.attack)
        print("Defense:", self.defense)
        print("Speed:", self.speed)
        print("Spc Atk:", self.special_attack)
        print("Spc Def:", self.special_defense)
        """

    def level_up(self):
        """Increases a Monster's level by one and increases stats
        accordingly

        :rtype: None
        :returns: None
        """
        logger.info("Leveling %s from %i to %i!" % (self.name, self.level, self.level + 1))
        # Increase Level and stats
        self.level += 1
        self.set_stats()

        # Learn New Moves
        for move in self.moveset:
            if move['level_learned'] >= self.level:
                logger.info("%s learned technique %i!" % (self.name, move['slug']))
                technique = Technique(move['slug'])
                self.learn(technique)

    def set_level(self, level=5):
        """Sets the Monster's level to the specified arbitrary level,
        and modifies experience accordingly.

        :param level: The level to set the monster to.

        :type level: Integer

        :rtype: None
        :returns: None

        **Example:**

        >>> bulbatux.set_level(20)
        """
        self.level = level
        self.total_experience = self.experience_required_modifier * self.level ** 3

        count = 0

        # For each level between 1 and current, calculate stats
        while count < self.level:
            count += 1
            self.set_stats()

    def load_sprites(self):
        """Loads the monster's sprite images as Pygame surfaces.

        :rtype: Boolean
        :returns: True if the sprites are already loaded.

        **Examples:**

        >>> bulbatux.load_sprites()
        >>> bulbatux.sprites

        """
        if len(self.sprites):
            return True

        self.sprites["front"] = tools.load_and_scale(self.front_battle_sprite)
        self.sprites["back"] = tools.load_and_scale(self.back_battle_sprite)
        self.sprites["menu"] = tools.load_and_scale(self.menu_sprite)

        return False
