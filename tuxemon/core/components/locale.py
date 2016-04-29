#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2016, William Edwards <shadowapex@gmail.com>,
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
# core.components.locale Component for handling in-game translations.
#

import logging
import json
import os
from core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

LOCALE_PATH = "resources/db/locale"
FALLBACK_LOCALE = "en_US"

class Translator(object):

    def __init__(self):
        self.locale = prepare.CONFIG.locale
        self.directories = self.discover()
        self.locale_files = self.get_locales(self.directories)
        self.translations = self.load_locale(self.locale, self.locale_files)
        self.fallback = self.load_locale(FALLBACK_LOCALE, self.locale_files)

    def discover(self):
        """Returns locale directories discovered in the base & user data directory

        :param: None

        :returns: List of discovered locale directories

        """
        directories = [prepare.BASEDIR + LOCALE_PATH]
        for item in os.listdir(prepare.USER_DATA_PATH):
            item = prepare.USER_DATA_PATH + "/" + item
            if os.path.isdir(item):
                locale_directory = item + LOCALE_PATH
                directories.append(locale_directory)

        return directories

    def get_locales(self, directories):
        """Discovers translation files found from locale directories.

        :param: None

        :returns: List of locale files

        """
        locale_files = []
        for d in directories:
            for locale_file in os.listdir(d):
                locale_file_path = d + "/" + locale_file
                if locale_file_path.endswith(".json") and os.path.isfile(locale_file_path):
                    locale_files.append(locale_file_path)

        return locale_files

    def load_locale(self, locale_name, locale_files):
        """Loads a language locale into the translator object

        :param locale_name: Name of the locale to load (E.g. "en_US")

        """
        translations = {}
        for locale_file in locale_files:
            filename = locale_file.split("/")[-1]
            if not filename.startswith(locale_name):
                continue
            try:
                f = open(locale_file, "r")
                data = json.load(f)
                f.close()
                translations = dict(data, **translations)
            except Exception as e:
                print("Unable to load translation:", e)

        return translations

    def has_key(self, key):
        if key in self.translations or key in self.fallback:
            return True
        else:
            return False

    def get_key(self, key):
        if key in self.translations:
            return self.translations[key]
        elif key in self.fallback:
            return self.fallback[key]
        else:
            logger.error("Key '%s' does not exist in '%s' locale file." % (key, self.locale))
            print("Key '%s' does not exist in '%s' locale file." % (key, self.locale))
            return None


    def change_locale(self, locale_name):
        """Changes the translator object to the given locale

        :param locale_name: Name of the locale to load (E.g. "en_US")

        """
        self.locale = locale_name
        self.directories = self.discover()
        self.locale_files = self.get_locales(self.directories)
        self.translations = self.load_locale(self.locale, self.locale_files)

    def format(self, text, parameters={}):
        """Replaces variables in a translation string with the given parameters.

        :param text: The translation string with parameters.
        :param parameters: A dictionary of variables to replace in the string.

        :returns: The formatted translation string.

        """
        for key, value in parameters.items():
            text = text.replace("${{" + key + "}}", value)

        return text

    def translate(self, key, parameters={}):
        """Returns translated text for the given key.

        :param key: Key in the locale JSON file of the translated text.
        :param parameters: Optional dictionary of text to replace in translated string.

        :returns: The translated string.

        """
        if key in self.translations:
            translation_text = self.translations[key]
        elif key in self.fallback:
            logger.warning("Key '%s' does not exist in '%s' locale file. Falling back to '%s'." %
                           (key, self.locale, FALLBACK_LOCALE))
            print("Key '%s' does not exist in '%s' locale file. Falling back to '%s'." %
                  (key, self.locale, FALLBACK_LOCALE))
            translation_text = self.fallback[key]
        else:
            logger.error("Key '%s' does not exist in '%s' locale file." % (key, self.locale))
            print("Key '%s' does not exist in '%s' locale file." % (key, self.locale))
            translation_text = "Locale Error"

        return self.format(translation_text, parameters)

translator = Translator()
