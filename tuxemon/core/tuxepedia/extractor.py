"""
    Tuxepedia HTML extractor

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

import logging
import os
import os.path
import shutil

from lxml import html
import requests

from . import WEB_PATHS, RESOURCE_PATHS


class TuxepediaWebExtractor:
    """requests + lxml wrapper class to extract Tuxemon
    information from the Tuxepedia website"""

    def __init__(self):

        self.tuxepedia_url = WEB_PATHS.tuxepedia
        self.db_connection = None

        # TODO: add more Web params, like 'Content-Type' as needed
        self.headers = {'User-agent': 'Mozilla/5.0'}

    def get_logger(self):
        """Access a custom class logger"""

        return logging.getLogger(self.__class__.__name__)

    def get_monsters(self):
        """Extract monster data from the Tuxepedia Wiki page

        :return: dict/JSON of the Tuxepedia monster entries
        """

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

            monsters[name] = {"url": self.get_monster_url(monster_row),
                              "types": self.get_monster_types(monster_row),
                              "sprites": self.get_monster_sprites(monster_row),
                              "blurp": self.get_monster_blurp(monster_row),
                              "call": self.get_monster_call(monster_row)}

        return monsters

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

    def get_monster_sprites(self, monster_row):
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

            local_sprite_path = os.path.join(RESOURCE_PATHS.monster_sprites,
                                             txmn_name,
                                             sprite_type + sprite_ext)

            self.url_to_file(sprite_url, local_sprite_path)

            # log output
            self.get_logger().debug("Stored {} sprite at {}".format(txmn_name,
                                                                    local_sprite_path))

            sprites[sprite_type] = True

        return sprites

    def get_monster_blurp(self, monster_row):
        """Get tuxemon description/blurp from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: tuxemon description/blurp text
        """

        return monster_row[8].text_content()

    def get_monster_call(self, monster_row):
        """Get tuxemon call/cry from Tuxepedia table row

        :param monster_row: HTML <tr> table row element
        :return: tuxemon call/cry URL
        """

        # get tuxemon name
        txmn_name = self.get_monster_name(monster_row)

        a = monster_row[9].find("a")

        # skip if no call or only a placeholder was found
        if a is None or a.text_content() == "Missing":
            return None

        href = a.get("href")

        # construct sound paths (full URL and local)
        cry_url = self.tuxepedia_url + href

        cry_ext = os.path.splitext(cry_url)[1]

        local_cry_path = os.path.join(RESOURCE_PATHS.monster_sounds,
                                      txmn_name,
                                      "cry" + cry_ext)

        self.url_to_file(cry_url, local_cry_path)

        # log output
        self.get_logger().debug("Stored {} sprite at {}".format(txmn_name,
                                                                local_cry_path))

        return True

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
