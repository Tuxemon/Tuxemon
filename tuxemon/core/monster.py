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
# core.monster Tuxemon monster module
#
#

import logging
import random
import uuid

from tuxemon.core import ai, fusion, graphics
from tuxemon.core.db import db
from tuxemon.core.locale import T
from tuxemon.core.technique import Technique

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "current_hp",
    "level",
    "name",
    "slug",
    "status",
    "total_experience",
    "flairs",
)

SHAPES = {
    "aquatic": {"armour": 8, "dodge": 4, "hp": 8, "melee": 6, "ranged": 6, "speed": 4,},
    "blob": {"armour": 8, "dodge": 4, "hp": 8, "melee": 4, "ranged": 8, "speed": 4,},
    "brute": {"armour": 7, "dodge": 5, "hp": 7, "melee": 8, "ranged": 4, "speed": 5,},
    "dragon": {"armour": 7, "dodge": 5, "hp": 6, "melee": 6, "ranged": 6, "speed": 6,},
    "flier": {"armour": 5, "dodge": 7, "hp": 4, "melee": 8, "ranged": 4, "speed": 8,},
    "grub": {"armour": 7, "dodge": 5, "hp": 7, "melee": 4, "ranged": 8, "speed": 5,},
    "humanoid": {
        "armour": 5,
        "dodge": 7,
        "hp": 4,
        "melee": 4,
        "ranged": 8,
        "speed": 8,
    },
    "hunter": {"armour": 4, "dodge": 8, "hp": 5, "melee": 8, "ranged": 4, "speed": 7,},
    "landrace": {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 8,
        "ranged": 4,
        "speed": 4,
    },
    "leviathan": {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 6,
        "ranged": 6,
        "speed": 4,
    },
    "polliwog": {
        "armour": 4,
        "dodge": 8,
        "hp": 5,
        "melee": 4,
        "ranged": 8,
        "speed": 7,
    },
    "serpent": {"armour": 6, "dodge": 6, "hp": 6, "melee": 4, "ranged": 8, "speed": 6,},
    "sprite": {"armour": 6, "dodge": 6, "hp": 4, "melee": 6, "ranged": 6, "speed": 8,},
    "varmint": {"armour": 6, "dodge": 6, "hp": 6, "melee": 8, "ranged": 4, "speed": 6,},
}

MAX_LEVEL = 999
MISSING_IMAGE = "gfx/sprites/battle/missing.png"


# class definition for tuxemon flairs:
class Flair:
    def __init__(self, category, name):
        self.category = category
        self.name = name


# class definition for first active tuxemon to use in combat:
class Monster:
    """A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.

    :param: None

    **Example:**

    >>> bulbatux = Monster()
    >>> bulbatux.load_from_db("Bulbatux")
    """

    def __init__(self, save_data=None):
        if save_data is None:
            save_data = dict()

        self.slug = ""
        self.name = ""  # The display name of the Tuxemon
        self.category = ""
        self.description = ""
        self.instance_id = uuid.uuid4()  # unique id for this specific, individual tuxemon

        self.armour = 0
        self.dodge = 0
        self.melee = 0
        self.ranged = 0
        self.speed = 0
        self.current_hp = 0
        self.hp = 0
        self.level = 0

        self.moves = []       # list of technique objects. Used in combat.
        self.moveset = []     # list of possible technique objects.
        self.evolutions = []  # list of possible evolution objects.
        self.flairs = {}      # dictionary of flairs, one is picked randomly.
        self.battle_cry = ""  # slug for a sound file, used primarly when they enter battle
        self.faint_cry = ""   # slug for a sound file, used when the monster faints
        self.ai = None
        self.owner = None     # set to NPC instance if they own it

        # The multiplier for experience
        self.experience_required_modifier = 1
        self.total_experience = 0

        self.type1 = "aether"
        self.type2 = None
        self.shape = "landrace"

        self.status = list()
        self.status_damage = 0
        self.status_turn = 0

        self.weight = 0

        # the multiplier for checks when a monster ball is thrown.
        self.catch_rate = 1

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
        self.menu_sprite_1 = ""
        self.menu_sprite_2 = ""

        self.set_state(save_data)
        self.set_stats()
        self.set_flairs()

    def load_from_db(self, slug):
        """Loads and sets this monster's attributes from the monster.db database.
        The monster is looked up in the database by name.

        :param slug: Slug to lookup
        :type slug: str

        :rtype: None
        """

        # Look up the monster by name and set the attributes in this instance
        results = db.lookup(slug, table="monster")

        if results is None:
            logger.error("monster {} is not found".format(slug))
            raise RuntimeError

        self.slug = results["slug"]                             # short English identifier
        self.name = T.translate(results["slug"])                # translated name
        self.description = T.translate("{}_description".format(results["slug"]))  # translated description
        self.category = T.translate(results["category"])        # translated category
        self.shape = results.get("shape", "landrace").lower()
        types = results.get("types")
        if types:
            self.type1 = results["types"][0].lower()
            if len(types) > 1:
                self.type2 = results["types"][1].lower()

        self.weight = results["weight"]

        # Look up the moves that this monster can learn AND LEARN THEM.
        moveset = results.get("moveset")
        if moveset:
            for move in moveset:
                self.moveset.append(move)
                if move["level_learned"] >= self.level:
                    technique = Technique(move["technique"])
                    self.learn(technique)

        # Look up the evolutions for this monster.
        evolutions = results.get("evolutions")
        if evolutions:
            for evolution in evolutions:
                self.evolutions.append(evolution)

        # Look up the monster's sprite image paths
        self.front_battle_sprite = self.get_sprite_path(results["sprites"]["battle1"])
        self.back_battle_sprite = self.get_sprite_path(results["sprites"]["battle2"])
        self.menu_sprite_1 = self.get_sprite_path(results["sprites"]["menu1"])
        self.menu_sprite_2 = self.get_sprite_path(results["sprites"]["menu2"])

        # get sound slugs for this monster, defaulting to a generic type-based sound
        self.combat_call = results.get("sounds", {}).get(
            "combat_call", "sound_{}_call".format(self.type1)
        )
        self.faint_call = results.get("sounds", {}).get(
            "faint_call", "sound_{}_faint".format(self.type1)
        )

        # Load the monster AI
        # TODO: clean up AI 'core' loading and what not
        ai_result = results["ai"]
        if ai_result == "SimpleAI":
            self.ai = ai.SimpleAI()
        elif ai_result == "RandomAI":
            self.ai = ai.RandomAI()

    def learn(self, technique):
        """Adds a technique to this tuxemon's moveset.

        :param technique: The core.monster.Technique object for
            the monster to learn.

        :type technique: tuxemon.core.monster.Technique

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

        # Level up worthy monsters
        while self.total_experience >= self.experience_required(1):
            self.level_up()

    def apply_status(self, status):
        """ Apply a status to the monster

        :type status: tuxemon.core.technique.Technique
        :rtype: None
        """
        self.status.append(status)

    def set_stats(self):
        """Sets the monsters initial stats, or improves stats
        when called during a level up.

        :rtype: None
        :returns: None

        """
        if self.level < 10:
            level = 10
        else:
            level = self.level

        multiplier = level + 7
        shape = SHAPES[self.shape]
        self.armour = shape["armour"] * multiplier
        self.dodge = shape["dodge"] * multiplier
        self.hp = shape["hp"] * multiplier
        self.melee = shape["melee"] * multiplier
        self.ranged = shape["ranged"] * multiplier
        self.speed = shape["speed"] * multiplier

    def level_up(self):
        """Increases a Monster's level by one and increases stats
        accordingly

        :rtype: None
        :returns: None
        """
        logger.info("Leveling %s from %i to %i!" % (self.name, self.level, self.level + 1))
        # Increase Level and stats
        self.level += 1
        self.level = min(self.level, MAX_LEVEL)
        self.set_stats()

        # Learn New Moves
        for move in self.moveset:
            if move["level_learned"] >= self.level:
                logger.info("{} learned technique {}!".format(self.name, move["technique"]))
                technique = Technique(move["technique"])
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
        self.total_experience = self.experience_required()
        self.set_stats()

    def experience_required(self, level_ofs=0):
        """Gets the experience requirement for the given level.

        :rtype: Integer
        :returns: Required exp
        """
        return self.experience_required_modifier * (self.level + level_ofs) ** 3

    def get_evolution(self, path):
        """Checks if an evolution is valid and gets the resulting monster.

        :rtype: String
        :returns: New monster slug if valid, None otherwise
        """
        for evolution in self.evolutions:
            if evolution['path'] == path:
                level_over = evolution['at_level'] > 0 and self.level >= evolution['at_level']
                level_under = evolution['at_level'] < 0 and self.level <= -evolution['at_level']
                if level_over or level_under:
                    return evolution["monster_slug"]
        return None

    def get_sprite(self, sprite, **kwargs):
        """Gets a specific type of sprite for the monster.

        :rtype: Pygame surface
        :returns: The surface of the monster sprite
        """
        if sprite == "front":
            surface = graphics.load_sprite(self.front_battle_sprite, **kwargs)
        elif sprite == "back":
            surface = graphics.load_sprite(self.back_battle_sprite, **kwargs)
        elif sprite == "menu":
            surface = graphics.load_animated_sprite([
                self.menu_sprite_1,
                self.menu_sprite_2],
                0.25, **kwargs)
        else:
            raise ValueError("Cannot find sprite for: {}".format(sprite))

        # Apply flairs to the monster sprite
        for flair in self.flairs.values():
            flair_path = self.get_sprite_path("gfx/sprites/battle/{}-{}-{}".format(self.slug, sprite, flair.name))
            if flair_path != MISSING_IMAGE:
                flair_sprite = graphics.load_sprite(flair_path, **kwargs)
                surface.image.blit(flair_sprite.image, (0, 0))

        return surface

    def set_flairs(self):
        """Sets the flairs of this monster if they were not already configured

        :rtype: None
        :returns: None
        """
        if len(self.flairs) > 0 or self.slug == "":
            return

        results = db.lookup(self.slug, table="monster")
        flairs = results.get("flairs")
        if flairs:
            for flair in flairs:
                flair = Flair(flair["category"], random.choice(flair["names"]))
                self.flairs[flair.category] = flair

    def get_sprite_path(self, sprite):
        """
        Paths are set up by convention, so the file extension is unknown.
        This adds the appropriate file extension if the sprite exists,
        and returns a dummy image if it can't be found.

        rtype: String
        returns: path to sprite or placeholder image
        """
        try:
            exts = ["png", "gif", "jpg", "jpeg"]
            for ext in exts:
                path = "%s.png" % sprite
                full_path = graphics.transform_resource_filename(path)
                if full_path:
                    return full_path
        except OSError:
            logger.debug("Could not find monster sprite {}".format(sprite))
            return MISSING_IMAGE

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

        self.sprites["front"] = graphics.load_and_scale(self.front_battle_sprite)
        self.sprites["back"] = graphics.load_and_scale(self.back_battle_sprite)
        self.sprites["menu"] = graphics.load_and_scale(self.menu_sprite_1)
        return False

    def get_state(self):
        """Prepares a dictionary of the monster to be saved to a file

        :param: None

        :rtype: Dictionary
        :returns: Dictionary containing all the information about the monster
        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id)

        if self.status:
            save_data["status"] = [i.get_state() for i in self.status]
        body = self.body.get_state()
        if body:
            save_data["body"] = body

        save_data["moves"] = [tech.slug for tech in self.moves]

        return save_data

    def set_state(self, save_data):
        """Loads information from saved data

        :param save_data: Data used to reconstruct the monster
        :type save_data: Dictionary

        :rtype: None
        :returns: None

        """
        if not save_data:
            return

        self.load_from_db(save_data["slug"])

        for key, value in save_data.items():
            if key == "status" and value:
                self.status = [Technique(slug=i) for i in value]
            elif key == "body" and value:
                self.body.set_state(value)
            elif key == "moves" and value:
                self.moves = [Technique(slug) for slug in value]
            elif key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)

        self.load_sprites()

    def end_combat(self):
        for move in self.moves:
            move.full_recharge()

        if "status_faint" in (s.slug for s in self.status):
            self.status = [Technique("status_faint")]
        else:
            self.status = []

    def speed_test(self, action):
        if action.technique.is_fast:
            return random.randrange(0, self.speed) * 1.5
        else:
            return random.randrange(0, self.speed)


def decode_monsters(json_data):
    return [Monster(save_data=mon) for mon in json_data.get("monsters") or []]


def encode_monsters(mons):
    return [mon.get_state() for mon in mons]
