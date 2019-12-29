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
# Andy Mender <andymenderunix@gmail.com>
#
#
# core.components.locale Component for handling in-game translations.
#

from __future__ import unicode_literals
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
import gettext
import io
import json
import logging
import os
import os.path

from tuxemon.constants import paths
from tuxemon.core.prepare import CONFIG

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"


class TranslatorPo(object):
    """gettext-based translator class."""

    def __init__(self):
        self.locale = CONFIG.locale
        self.translate = None
        self.languages = self.collect_languages()
        self.build_translations()
        self.load_locale(CONFIG.locale)

    def collect_languages(self):
        """Collect languages/locales with available translation files."""
        languages = []

        for ld in os.listdir(paths.L18N_DIR):
            ld_full_path = os.path.join(paths.L18N_DIR, ld)

            if os.path.isdir(ld_full_path):
                languages.append(ld)

        return languages

    def build_translations(self):
        """Create MO files for existing PO translation files."""

        for ld in self.languages:
            infile = os.path.join(paths.L18N_DIR, ld, "LC_MESSAGES", "base.po")
            outfile = os.path.join(os.path.dirname(infile), "base.mo")

            # build only complete translations
            if os.path.exists(infile):
                with open(infile, "r", encoding="UTF8") as po_file, open(outfile, "wb") as mo_file:
                    catalog = read_po(po_file)
                    write_mo(mo_file, catalog)

    def load_locale(self, locale_name="en_US"):
        """Load a selected locale for translation.

        :param locale_name: name of the chosen locale
        """

        # init and load requested language translation (if exists)
        if locale_name in self.languages:
            trans = gettext.translation("base", localedir=paths.L18N_DIR, languages=[locale_name])

            # update locale
            self.locale = locale_name

        else:
            logger.warning("Locale {} not found. Using fallback.".format(locale_name))
            trans = gettext.translation("base", localedir=paths.L18N_DIR, languages=[FALLBACK_LOCALE])

            # fall back to default locale
            self.locale = FALLBACK_LOCALE

        trans.install()

        self.translate = trans.gettext

    def format(self, text, parameters={}):
        """Replaces variables in a translation string with the given parameters.

        :param text: The translation string with parameters.
        :param parameters: A dictionary of variables to replace in the string.

        :returns: The formatted translation string.

        """
        # fix escaped newline symbols
        text = text.replace(r"\n", "\n")

        # translate input text if locale was loaded or force-load locale and translate
        if self.translate is not None:
            text = self.translate(text)
        else:
            self.load_locale(self.locale)
            text = self.translate(text)         # self.load_locale populates self.translate

        # apply parameters only if non-empty
        if parameters:
            return text.format(**parameters)
        else:
            return text


class Translator(object):

    def __init__(self):
        # immediately grab fallback if 'locale' missing in config
        self.locale = CONFIG.locale or FALLBACK_LOCALE

        self.directories = self.discover_locale_dirs()
        self.locale_files = self.get_locales(self.directories)
        self.translations = self.load_locale(self.locale, self.locale_files)

        self.fallback = self.load_locale(FALLBACK_LOCALE, self.locale_files)

    def discover_locale_dirs(self):
        """Returns locale directories discovered in the base & user data directory

        :returns: List of discovered locale directories

        """
        directories = [os.path.join(paths.BASEDIR, paths.LOCALE_PATH)]

        # TODO: use os.walk if second level directories are needed?
        for item in os.listdir(paths.USER_GAME_DATA_DIR):
            item = os.path.join(paths.USER_GAME_DATA_DIR, item)

            # TODO: filter also by directory name?
            if os.path.isdir(item):
                locale_directory = os.path.join(item, paths.LOCALE_PATH)

                directories.append(locale_directory)

        return directories

    def get_locales(self, directories):
        """Discovers translation files found in locale directories.

        :param directories: list of directories containing locale JSON data

        :returns: list of locale file paths

        """
        locale_files = []

        for d in directories:
            for locale_file in os.listdir(d):
                locale_file_path = os.path.join(d, locale_file)

                if os.path.isfile(locale_file_path) and locale_file_path.endswith(".json"):
                    locale_files.append(locale_file_path)

        return locale_files

    def load_locale(self, locale_name, locale_files):
        """Loads a language locale into the translator object

        :param locale_name: name of the locale to load (E.g. "en_GB")

        """
        translations = {}

        for locale_file in locale_files:
            filename = os.path.splitext(os.path.basename(locale_file))[0]

            if filename != locale_name:
                continue

            try:
                with io.open(locale_file, "r", encoding="UTF-8") as f:
                    data = json.load(f)

                translations.update(data)
            except Exception as e:
                logger.error("Unable to load translation:", e)

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
            return None


    def change_locale(self, locale_name):
        """Changes the translator object to the given locale

        :param locale_name: Name of the locale to load (E.g. "en_GB")

        """
        self.locale = locale_name
        self.directories = self.discover_locale_dirs()
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
            translation_text = self.fallback[key]
        else:
            logger.error("Key '%s' does not exist in '%s' locale file." % (key, self.locale))
            translation_text = "Locale Error"

        return self.format(translation_text, parameters)

translator = Translator()

T = TranslatorPo()
