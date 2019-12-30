# coding=utf-8
"""
    Tuxepedia HTML extractor

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import os.path
import shutil
from sys import version_info

import requests
from lxml import html

assert version_info[0] == 3, "Use Python 3 for this script"

from . import WEB_PATHS, RESOURCE_PATHS

logging.basicConfig(level=logging.INFO)

class TuxepediaWebExtractor:
    """requests + lxml wrapper class to extract Tuxemon
    information from the Tuxepedia website"""

    def __init__(self):

        self.tuxepedia_url = WEB_PATHS.tuxepedia
        self.db_connection = None
        self.completed_monsters = True

        # TODO: add more Web params, like 'Content-Type' as needed
        self.headers = {'User-agent': 'Mozilla/5.0'}

    def get_logger(self):
        """Access a custom class logger"""

        return logging.getLogger(self.__class__.__name__)

    def get_completed_monsters(self):
        """Extract monster data from the Tuxepedia Wiki page

        :return: dict/JSON of the Tuxepedia monster entries
        """
        self.completed_monsters = True

        monsters = {}

        monsters_tree = self.url_to_html(self.tuxepedia_url,
                                         {"title": "Completed_Tuxemon"})

        table = monsters_tree.xpath(WEB_PATHS.monsters_xpath)[0]

        # extract monster records ("tr", table row HTML blocks) from the table
        for monster_row in table.findall("tr"):
            try:
                # ignore elements which are not actual table rows
                if "data-row-number" not in monster_row.attrib:
                    continue

                # construct monster JSON entry
                name = self.get_monster_name(monster_row)
                safe_name = fix_name(name.lower())

                self.get_logger().info(name)
                self.get_complete_monster_sprites(monster_row)
                monsters[name] = {
                    "slug": safe_name,
                    "category": fix_name(self.get_monster_category(monster_row).lower()),
                    "ai": "RandomAI",
                    # "blurp": self.get_monster_blurp(monster_row),
                    # "call": self.get_monster_call(monster_row),
                    # "moveset": [],
                    "shape": self.get_monster_shape(monster_row),
                    # "tuxepedia_url": self.get_monster_url(monster_row),
                    "types": self.get_monster_types(monster_row),
                    "weight": 25,
                }
            except Exception as e:
                self.get_logger().warning(e)

        return monsters

    def get_monsters(self):
        """Extract monster data from the Tuxepedia Wiki page

        :return: dict/JSON of the Tuxepedia monster entries
        """
        self.completed_monsters = False

        monsters = {}

        monsters_tree = self.url_to_html(self.tuxepedia_url,
                                         {"title": "Creature_Progress_Tracker"})

        table = monsters_tree.xpath(WEB_PATHS.monsters_xpath)[0]

        # extract monster records ("tr", table row HTML blocks) from the table
        for monster_row in table.findall("tr"):

            # ignore elements which are not actual table rows
            if "data-row-number" not in monster_row.attrib:
                continue

            # construct monster JSON entry
            name = self.get_monster_name(monster_row)

            monsters[name] = {"tuxepedia_url": self.get_monster_url(monster_row),
                              "types": self.get_monster_types(monster_row),
                              "sprites": self.get_incomplete_monster_sprites(monster_row),
                              "blurp": self.get_monster_blurp(monster_row),
                              "call": self.get_monster_call(monster_row)}

        return monsters

    def get_monster_category(self, monster_row):
        """Get tuxemon types/elements from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: list of tuxemon types/elements
        """

        # get all type elements (<a> blocks)
        types = monster_row[3].findall("a")

        categories = [el.text_content() for el in types] or ['']
        return categories[0]

    def get_monster_name(self, monster_row):
        """Get tuxemon name from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: monster name
        """

        return monster_row[0][0].text_content()

    def get_monster_url(self, monster_row):
        """Get tuxemon entry URL from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: monster record URL in Tuxepedia
        """

        href = monster_row[0][0].get("href")

        # combine subindex URL with main website URL
        return self.tuxepedia_url + href

    def get_monster_types(self, monster_row):
        """Get tuxemon types/elements from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: list of tuxemon types/elements
        """

        # get all type elements (<a> blocks)
        types = monster_row[2].findall("a")

        # no type defined - type "Untyped"
        # TODO: intended behavior or leave list of types empty?
        if len(types) == 0:
            return ["Untyped"]

        # extract tyoe names
        return [el.text_content() for el in types]

    def get_complete_monster_sprites(self, monster_row):
        """Get tuxemon sprites from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: dict/JSON of tuxemon sprites
        """

        monster_url = self.get_monster_url(monster_row)
        monster_page = self.url_to_html(monster_url, {})
        table = monster_page.xpath(WEB_PATHS.monster_main_sprites)[0]
        rows = table.findall("tr")
        main_sprites_table = rows[0]
        face_sprites_table = rows[1]

        txmn_name = fix_name(self.get_monster_name(monster_row)).replace("_", "-")

        # sprites JSON template
        sprites = {
            "battle1": None,
            "battle2": None,
            "menu1": None,
            "menu2": None,
        }

        full_path = {
            "battle1": "gfx/sprites/battle/{}-front.png",
            "battle2": "gfx/sprites/battle/{}-back.png",
            "menu1": "gfx/sprites/battle/{}-menu01.png",
            "menu2": "gfx/sprites/battle/{}-menu02.png"
        }

        name = {
            "battle1": "{}-front.png",
            "battle2": "{}-back.png",
            "menu1": "{}-menu01.png",
            "menu2": "{}-menu02.png"
        }

        for sprite_type, el in zip(sprites, main_sprites_table[1:3] + face_sprites_table[1:3]):
            a = el.find("a")

            # skip if no sprite was found
            if a is None:
                self.get_logger().warning("%s not found for %s", sprite_type, txmn_name)
                continue

            img = a.find("img")

            # skip if sprite is defined as "Missing"
            if img is None:
                continue

            # construct sprite paths (full URL and local)
            sprite_url = self.tuxepedia_url + img.get("src")

            n = name[sprite_type].format(txmn_name.lower())

            local_sprite_path = os.path.join(RESOURCE_PATHS.monster_sprites, n)

            # download tuxemon sprite
            self.url_to_file(sprite_url, local_sprite_path)

            # log output
            self.get_logger().debug("Stored %s sprite at %s", txmn_name, local_sprite_path)

            sprites[sprite_type] = full_path[sprite_type].format(txmn_name.lower())

        return sprites

    def get_incomplete_monster_sprites(self, monster_row):
        """Get tuxemon sprites from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: dict/JSON of tuxemon sprites
        """

        # get tuxemon name
        txmn_name = self.get_monster_name(monster_row)

        # sprites JSON template
        sprites = {"battle1": None,
                   "battle2": None,
                   "menu1": None,
                   "menu2": None}

        for sprite_type, el in zip(sprites, monster_row[4:8]):
            a = el.find("a")

            # skip if no sprite was found
            if a is None:
                continue

            img = a.find("img")

            # skip if sprite is defined as "Missing"
            if img is None:
                continue

            # TODO: make sprite file values more meaningful
            sprite_img = os.path.basename(img.get("src"))

            # construct sprite paths (full URL and local)
            sprite_url = self.tuxepedia_url + img.get("src")

            sprite_ext = os.path.splitext(sprite_img)[1]

            sprite_file = sprite_type + sprite_ext

            local_sprite_path = os.path.join(RESOURCE_PATHS.monster_sprites,
                                             txmn_name.lower(),
                                             sprite_file)

            # download tuxemon sprite
            self.url_to_file(sprite_url, local_sprite_path)

            # log output
            self.get_logger().debug("Stored {} sprite at {}".format(txmn_name,
                                                                    local_sprite_path))

            sprites[sprite_type] = sprite_file

        return sprites

    def get_monster_shape(self, monster_row):
        """Get tuxemon description/blurp from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: tuxemon description/blurp text
        """

        return monster_row[4].text_content()

    def get_monster_blurp(self, monster_row):
        """Get tuxemon description/blurp from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: tuxemon description/blurp text
        """

        if self.completed_monsters:
            return monster_row[5].text_content()
        else:
            return monster_row[8].text_content()

    def get_monster_call(self, monster_row):
        """Get tuxemon call/cry from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: tuxemon call/cry URL
        """

        # get tuxemon name
        try:
            txmn_name = self.get_monster_name(monster_row)

            if self.completed_monsters:
                a = monster_row[6].find("a")
            else:
                a = monster_row[9].find("a")

            # skip if no call or only a placeholder was found
            if a is None or a.text_content() == "Missing":
                return None

            # get link to the sound file Tuxepedia entry
            href = a.get("href")

            # extract the direct URL to the sound file
            sound_entry = self.url_to_html(self.tuxepedia_url + href, params={})
            sound = sound_entry.xpath(WEB_PATHS.monster_sound_xpath)[0]
            sound_url = sound.get("href")

            # construct sound paths (full URL and local)
            cry_url = self.tuxepedia_url + sound_url

            cry_ext = os.path.splitext(cry_url)[1]

            cry_file = "cry" + cry_ext

            local_cry_path = os.path.join(RESOURCE_PATHS.monster_sounds,
                                          txmn_name.lower(), cry_file)

            # download tuxemon sound
            self.url_to_file(cry_url, local_cry_path)

            # log output
            self.get_logger().debug("Stored {} sprite at {}".format(txmn_name,
                                                                    local_cry_path))
            return cry_file
        except Exception as e:
            self.get_logger().warning(e)

    def url_to_html(self, url, params, headers = None):
        """Extract Web content into an HTML tree object

        :param url: URL path string
        :param params: requests auxiliary params
        :param headers: extra header fields needed for the request
        :return: HTML tree object or None on failure
        """

        content = self._exec_request(url, params, headers)

        if content is None:
            self.get_logger().warning("Couldn't retrieve"
                                      " content from {}".format(url))
            return None

        return html.fromstring(content)

    def url_to_file(self, url, file_path):
        """Extract Web content into a local file

        :param url: URL path string
        :param file_path: local file path target
        :return:
        """

        # extract Web content as byte stream
        byte_stream = self._exec_request(url, params={}, stream=True)

        # make sure the directories exist!
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # write byte stream to file in binary mode
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(byte_stream, out_file)

    def _exec_request(self, url, params, headers = None, stream = False):
        """Extract Web content

        :param url: URL path string
        :param params: requests auxiliary params
        :param headers: extra header fields needed for the request
        :param stream: toggle for extracting byte streams directly
        :return: request object/JSON or None on failure
        """

        if headers is None:
            headers = self.headers
        else:
            headers = {**self.headers, **headers}

        response = requests.get(url, params=params, headers=headers, stream=stream)

        if response.status_code != 200:
            return None

        if stream:
            return response.raw

        return response.content


def fix_name(name):
    return name.replace(" ♂", "_male").replace(" ♀", "_female").replace(" ", "_")
