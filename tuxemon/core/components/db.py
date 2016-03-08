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
# core.components.db Database handling module.
#
#

import json
import logging
import os

from core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class JSONDatabase(object):
    """Handles connecting to the game database for resources such as monsters,
    stats, etc.

    """

    def __init__(self):
        self.path = prepare.BASEDIR + "resources/db/"
        self.database = {"item": {},
                         "monster": {},
                         "npc": {},
                         "technique": {},
                         "encounter": {}}


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
        else:
            self.load_json(directory)


    def load_json(self, directory):
        """Loads all JSON items under a specified path.

        :param directory: The directory under resources/db/ to look in.
        :type directory: String

        :returns: None

        """

        for json_item in os.listdir(self.path + directory):

            # Only load .json files.
            if not json_item.endswith(".json"):
                continue

            # Load our json as a dictionary.
            file = open(self.path + directory + "/" + json_item, 'r')
            item = json.load(file)

            if item['id'] not in self.database[directory]:
                self.database[directory][item['id']] = item
            else:
                print(item, json)
                raise Exception("Error: Item with this id was already loaded.")
            file.close()


    def lookup(self, name, table="monster"):
        """Looks up a monster, technique, item, or npc based on name or id.

        :param name: The name of the monster, technique, item, or npc.
        :param table: Which index to do the search in. Can be: "monster",
            "item", "npc", or "technique".
        :type name: String
        :type table: String

        :rtype: Dict
        :returns: A dictionary from the resulting lookup.

        """
        if name in self.database[table]:
            return self.database[table][name]

        for id, item in self.database[table].items():
            if item['name'] == name:
                return item


    def lookup_by_id(self, id, table="monster"):
        """This is a legacy method from using the sqlite database. You should
        do this instead by calling JSONDatabase.database["monster"][id]

        :param id: The monster ID or technique ID to look up.
        :type id: Integer

        :rtype: List
        :returns: A list of monsters or techniques

        """
        logger.warning("lookup_by_id is deprecated. Use JSONDatabase.database")
        self.lookup(id, table)


    def lookup_sprite(self, monster_id, table="sprite"):
        """Looks up a monster's sprite image paths based on monster ID.
        NOTE: This method has been deprecated. Use the following instead:
        JSONDatabase.database['monster'][id]['sprites']

        :param monster_id: The monster ID to look up.
        :type monster_id: Integer

        :rtype: List
        :returns: A list of sprites

        """

        logger.warning("lookup_sprite is deprecated. Use JSONDatabase.database")
        results = {'sprite_battle1': self.database['monster'][monster_id]['sprites']['battle1'],
                   'sprite_battle2': self.database['monster'][monster_id]['sprites']['battle2'],
                   'sprite_menu1': self.database['monster'][monster_id]['sprites']['menu1']}

        return results

