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
# core.db Database handling module.
#
#


import json
import logging
import os
from operator import itemgetter

from tuxemon.core import prepare

logger = logging.getLogger(__name__)


def process_targets(json_targets):
    """ Return values in order of preference for targeting things.

    example: ["own monster", "enemy monster"]

    :param json_targets:
    :return:
    """

    return list(map(itemgetter(0), filter(itemgetter(1), sorted(json_targets.items(), key=itemgetter(1), reverse=True))))


class JSONDatabase:
    """Handles connecting to the game database for resources such as monsters,
    stats, etc.

    """

    def __init__(self, dir="all"):
        self.path = None
        self.database = {
            "item": {},
            "monster": {},
            "npc": {},
            "technique": {},
            "encounter": {},
            "inventory": {},
            "environment": {},
            "sounds": {},
            "music": {}
        }
        self.load(dir)

    def load(self, directory="all"):
        """Loads all data from JSON files located under our data path.

        :param directory: The directory under resources/db/ to load. Defaults
            to "all".
        :type directory: String

        :returns: None

        """

        self.path = prepare.fetch("db")
        if directory == "all":
            self.load_json("item")
            self.load_json("monster")
            self.load_json("npc")
            self.load_json("technique")
            self.load_json("encounter")
            self.load_json("inventory")
            self.load_json("environment")
            self.load_json("sounds")
            self.load_json("music")
        else:
            self.load_json(directory)

    def load_json(self, directory):
        """Loads all JSON items under a specified path.

        :param directory: The directory under resources/db/ to look in.
        :type directory: String

        :returns: None

        """

        for json_item in os.listdir(os.path.join(self.path, directory)):

            # Only load .json files.
            if not json_item.endswith(".json"):
                continue

            # Load our json as a dictionary.
            with open(os.path.join(self.path, directory, json_item)) as fp:
                try:
                    item = json.load(fp)
                except ValueError:
                    logger.error("invalid JSON " + json_item)
                    raise

            if type(item) is list:
                for sub in item:
                    self.load_dict(sub, directory)
            else:
                self.load_dict(item, directory)
              
    def load_dict(self, item, table):
        """Loads a single json object as a dictionary and adds it to the appropriate db table

        :param item: The json object to load in
        :type item: dict
        :param table: The db table to load the object into
        :type table: String

        :returns None

        """

        if item['slug'] not in self.database[table]:
            self.database[table][item['slug']] = item
        else:
            logger.warning("Error: Item with slug %s was already loaded.", item)

    def lookup(self, slug, table="monster"):
        """Looks up a monster, technique, item, or npc based on slug.

        :param slug: The slug of the monster, technique, item, or npc.  A short English identifier.
        :param table: Which index to do the search in. Can be: "monster",
            "item", "npc", or "technique".
        :type slug: String
        :type table: String

        :rtype: Dict
        :returns: A dictionary from the resulting lookup.

        """
        return set_defaults(
            self.database[table][slug],
            table
        )

    def lookup_file(self, table, slug):
        """Does a lookup with the given slug in the given table, expecting a dictionary with two keys, 'slug' and 'file'

        :param slug: The slug of the file record.
        :param table: The table to do the lookup in, such as "sounds" or "music"
        :type slug: String
        :type table: String

        :rtype: String
        :returns: The 'file' property of the resulting dictionary OR the slug if it doesn't exist.
        """

        filename = self.database[table][slug]["file"] or slug
        if (filename == slug):
            logger.debug("Could not find a file record for slug {}, did you remember to create a database record?".format(slug))

        return filename

    def lookup_sprite(self, slug, table="sprite"):
        """Looks up a monster's sprite image paths based on monster slug.
        NOTE: This method has been deprecated. Use the following instead:
        JSONDatabase.database['monster'][slug]['sprites']

        :param slug: The monster ID to look up.
        :type slug: String
        :param slug: The monster slug to look up.
        :type slug: String

        :rtype: List
        :returns: A list of sprites

        """

        logger.warning("lookup_sprite is deprecated. Use JSONDatabase.database")
        results = {'sprite_battle1': self.database['monster'][slug]['sprites']['battle1'],
                   'sprite_battle2': self.database['monster'][slug]['sprites']['battle2'],
                   'sprite_menu1': self.database['monster'][slug]['sprites']['menu1']}

        return results


def set_defaults(results, table):
    if table == "monster":
        name = results['slug']

        sprites = results.setdefault(
            "sprites",
            {}
        )

        for key, view in (
                ('battle1', 'front'),
                ('battle2', 'back'),
                ('menu1', 'menu01'),
                ('menu2', 'menu02'),
        ):
            if not results.get(key):
                sprites[key] = "gfx/sprites/battle/{}-{}".format(
                    name,
                    view
                )

    return results

# Global database container
db = JSONDatabase()
