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
# core.components.db Database handling module.
#
#

import json
import logging
import os

from operator import itemgetter

from tuxemon.constants import paths

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


def process_targets(json_targets):
    """ Return values in order of preference for targeting things.

    example: ["own monster", "enemy monster"]

    :param json_targets:
    :return:
    """

    return list(map(itemgetter(0), filter(itemgetter(1), sorted(json_targets.items(), key=itemgetter(1), reverse=True))))


class JSONDatabase(object):
    """Handles connecting to the game database for resources such as monsters,
    stats, etc.

    """

    def __init__(self, dir=None):
        self.path = paths.DB_DIR
        self.database = {
            "item": {},
            "monster": {},
            "npc": {},
            "technique": {},
            "encounter": {},
            "inventory": {},
        }
        if dir:
            self.load(dir)

    def load(self, directory="all"):
        """Loads all data from JSON files located under our data path.

        :param directory: The directory under resources/db/ to load. Defaults
            to "all".
        :type directory: String

        :returns: None

        """

        if directory == "all":
            self.load_json("item")
            self.load_json("monster")
            self.load_json("technique")
            self.load_json("npc")
            self.load_json("encounter")
            self.load_json("inventory")
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

            if item['slug'] not in self.database[directory]:
                self.database[directory][item['slug']] = item
            else:
                logger.error(item, json)
                raise Exception("Error: Item with this slug was already loaded.")


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
