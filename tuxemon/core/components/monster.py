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
import os
import pprint
import random

from core import prepare
from core import tools
from . import db
from . import fusion

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
         'monster_id': 1,
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

        self.name = ""          # The display name of the Tuxemon
        self.monster_id = 0
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

    def load_from_db(self, name):
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
        results = monsters.lookup(name)

        self.name = results["name"]
        self.monster_id = results["id"]
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
                technique = Technique(id=move['technique_id'])
                self.learn(technique)

        # Look up the monster's sprite image paths
        self.front_battle_sprite = results['sprites']['battle1']
        self.back_battle_sprite = results['sprites']['battle2']
        self.menu_sprite = results['sprites']['menu1']

    def load_sprite_from_db(self):
        """Looks up the path to the monster's battle sprites so they can be
        loaded as pygame surfaces.

        :param: None

        :rtype: None
        :returns: None

        """

        # Look up the monster's sprite image paths
        results = monsters.lookup_sprite(self.monster_id)

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
        #Increase Level and stats
        self.level += 1
        self.set_stats()

        #Learn New Moves
        for move in self.moveset:
            if move['level_learned'] >= self.level:
                logger.info("%s learned technique id %i!" % (self.name, move['technique_id']))
                technique = Technique(id=move['technique_id'])
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

        :param scale: Amount to scale the sprite when loading the image.
        :type scale: Integer

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


class Technique(object):
    """A technique object is a particular skill that tuxemon monsters can use
    in battle.

    **Example:**

    >>> poison_tech = Technique("Poison Sting")
    >>> pprint.pprint(poison_tech.__dict__)
        {'category': u'special',
         'effect': [u'poison', u'damage'],
         'name': u'Poison Sting',
         'power': 40,
         'tech_id': 2,
         'type1': u'Poison',
         'type2': None}

    """

    def __init__(self, name=None, id=None):
        self.name = "Pound"
        self.tech_id = 0
        self.category = "attack"
        self.type1 = "Normal"
        self.type2 = None
        self.power = 1
        self.effect = []

        # If a name of the technique was provided, autoload it.
        if name or id:
            self.load(name, id)

    def load(self, name, id):
        """Loads and sets this technique's attributes from the technique
        database. The technique is looked up in the database by name or id.

        :param name: The name of the technique to look up in the monster
            database.
        :param id: The id of the technique to look up in the monster database.

        :type name: String
        :type id: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>>

        """

        if name:
            results = monsters.lookup(name, table="technique")
        elif id:
            results = monsters.database['technique'][id]

        self.name = results["name"]
        self.tech_id = results["id"]
        self.category = results["category"]

        self.type1 = results["types"][0]
        if len(results['types']) > 1:
            self.type2 = results["types"][1]
        else:
            self.type2 = None

        self.power = results["power"]
        self.effect = results["effects"]

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

        :rtype: bool
        :returns: If technique was successful or not

        **Examples:**

        >>> poison_tech = Technique("Poison Sting")
        >>> bulbatux.learn(poison_tech)
        >>>
        >>> bulbatux.moves[0].use(user=bulbatux, target=tuxmander)
        """
        # Loop through all the effects of this technique and execute the effect's function.
        # TODO: more robust API
        successful = False
        for effect in self.effect:
            if getattr(self, str(effect))(user, target):
                successful = True

        return successful

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
            target.status_turn += 1
            if target.status_turn > 1:
                return int(self.power)
            return 0

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
        already_poisoned = any(t for t in target.status if t.name == "Poison")

        if not already_poisoned and random.randrange(1, 2) == 1:
            poison = Technique("Poison")
            target.status.append(poison)
            target.status_turn = 0
            target.status_damage = self.power
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
        already_fainted = any(t for t in target.status if t.name == "Faint")

        if already_fainted:
            raise RuntimeError
        else:
            status = Technique("Faint")
            target.status.append(status)
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
