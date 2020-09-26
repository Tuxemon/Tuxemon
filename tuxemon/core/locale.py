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
# core.locale Component for handling in-game translations.
#


import gettext
import io
import json
import logging
import os
import os.path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from tuxemon.constants import paths
from tuxemon.core import prepare

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"


class TranslatorPo:
    """gettext-based translator class."""

    def __init__(self):
        self.locale = prepare.CONFIG.locale
        self.translate = self._lazy_load
        self.languages = []

    def _lazy_load(self, *args, **kwargs):
        # this is a hack to let cx_freeze work
        self.collect_languages(prepare.CONFIG.recompile_translations)
        return self.translate(*args, **kwargs)

    def collect_languages(self, recompile_translations=False):
        """Collect languages/locales with available translation files."""
        self.languages = []

        for ld in os.listdir(prepare.fetch("l18n")):
            ld_full_path = os.path.join(prepare.fetch("l18n"), ld)

            if os.path.isdir(ld_full_path):
                self.languages.append(ld)

        self.build_translations(recompile_translations)
        self.load_locale(prepare.CONFIG.locale)

    def build_translations(self, recompile_translations=False):
        """Create MO files for existing PO translation files."""

        for ld in self.languages:
            infile = os.path.join(prepare.fetch("l18n"), ld, "LC_MESSAGES", "base.po")
            outfile = os.path.join(os.path.dirname(infile), "base.mo")

            # build only complete translations
            if os.path.exists(infile) and (
                    not os.path.exists(outfile) or recompile_translations):
                with open(infile, "r", encoding="UTF8") as po_file:
                    catalog = read_po(po_file)
                with open(outfile, "wb") as mo_file:
                    write_mo(mo_file, catalog)

    def load_locale(self, locale_name="en_US"):
        """Load a selected locale for translation.

        :param locale_name: name of the chosen locale
        """

        # init and load requested language translation (if exists)
        if locale_name in self.languages:
            trans = gettext.translation("base", localedir = prepare.fetch("l18n"), languages=[locale_name])

            # update locale
            self.locale = locale_name

        else:
            logger.warning("Locale {} not found. Using fallback.".format(locale_name))
            trans = gettext.translation("base", localedir = prepare.fetch("l18n"), languages=[FALLBACK_LOCALE])

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

    def maybe_translate(self, text):
        """ Try to translate the text. If None, return empty string

        :param Optional[str] text: Text to translate
        :rtype: str
        """
        if text is None:
            return ""
        else:
            return self.translate(text)

class Translator:

    def __init__(self):
        # immediately grab fallback if 'locale' missing in config
        self.locale = prepare.CONFIG.locale or FALLBACK_LOCALE

        self.directories = self.discover_locale_dirs()
        self.locale_files = self.get_locales(self.directories)
        self.translations = self.load_locale(self.locale, self.locale_files)

        self.fallback = self.load_locale(FALLBACK_LOCALE, self.locale_files)

    def discover_locale_dirs(self):
        """Returns locale directories discovered in the base & user data directory

        :returns: List of discovered locale directories

        """
        directories = [prepare.fetch("db", "locale")]

        # TODO: use os.walk if second level directories are needed?
        for item in os.listdir(paths.USER_GAME_DATA_DIR):
            item = os.path.join(paths.USER_GAME_DATA_DIR, item)

            # TODO: filter also by directory name?
            if os.path.isdir(item):
                locale_directory = prepare.fetch(item, "db", "locale")

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
                with open(locale_file, "r", encoding="UTF-8") as f:
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
            logger.error("Key '{}' does not exist in '{}' locale file.".format(key, self.locale))
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
            logger.error("Key '{}' does not exist in '{}' locale file.".format(key, self.locale))
            translation_text = "Locale Error"

        return self.format(translation_text, parameters)


T = TranslatorPo()


def replace_text(session, text):
    """ Replaces ${{var}} tiled variables with their in-session value.

    :param tuxemon.core.session.Session session: Session
    :param str text: Raw text from the map

    :rtype: str

    **Examples:**

    >>> replace_text("${{name}} is running away!")
    'Red is running away!'

    """
    text = text.replace("${{name}}", session.player.name)
    text = text.replace(r"\n", "\n")

    for i in range(len(session.player.monsters)):
        monster = session.player.monsters[i]
        text = text.replace("${{monster_" + str(i) + "_name}}", monster.name)
        text = text.replace("${{monster_" + str(i) + "_desc}}", monster.description)
        text = text.replace("${{monster_" + str(i) + "_type}}", monster.slug)
        text = text.replace("${{monster_" + str(i) + "_category}}", monster.category)
        text = text.replace("${{monster_" + str(i) + "_shape}}", monster.shape)
        text = text.replace("${{monster_" + str(i) + "_hp}}", str(monster.current_hp))
        text = text.replace("${{monster_" + str(i) + "_hp_max}}", str(monster.hp))
        text = text.replace("${{monster_" + str(i) + "_level}}", str(monster.level))

    return text


def process_translate_text(session, text_slug, parameters):
    replace_values = {}

    # extract INI-style params
    for param in parameters:
        key, value = param.split("=")

        # TODO: is this code still valid? Translator class is NOT iterable
        """
        # Check to see if param_value is translatable
        if value in translator:
            value = trans(value)
        """
        # match special placeholders like ${{name}}
        replace_values[key] = replace_text(session, value)

    # generate translation
    text = T.format(text_slug, replace_values)

    # clear the terminal end-line symbol (multi-line translation records)
    text = text.rstrip("\n")

    # split text into pages for scrolling
    pages = text.split("\n")

    # generate scrollable text
    return [replace_text(session, page) for page in pages]
