# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import dataclasses
import gettext
import logging
import os
import os.path
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from gettext import GNUTranslations
from typing import Any, Optional

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from tuxemon import db, prepare
from tuxemon.constants import paths
from tuxemon.formula import convert_ft, convert_km, convert_lbs, convert_mi
from tuxemon.session import Session

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"
LOCALE_DIR = "l18n"


@dataclasses.dataclass(frozen=True, order=True)
class LocaleInfo:
    """Information about a locale."""

    locale: str
    category: str
    domain: str
    path: str


class LocaleFinder:
    """
    A class used to find and manage locales.

    This class is responsible for searching for locales in a given directory
    and providing information about the found locales.
    """

    def __init__(self, root_dir: str) -> None:
        self.root_dir = root_dir
        self.locale_names: set[str] = set()

    def search_locales(self) -> Generator[LocaleInfo, Any, None]:
        """
        Searches for locales in the given directory.

        Yields:
            LocaleInfo: Information about each found locale.
        """
        logger.debug("searching locales...")
        for locale in os.listdir(self.root_dir):
            self.locale_names.add(locale)
            locale_path = os.path.join(self.root_dir, locale)
            if os.path.isdir(locale_path):
                for category in os.listdir(locale_path):
                    category_path = os.path.join(locale_path, category)
                    if os.path.isdir(category_path):
                        for name in os.listdir(category_path):
                            path = os.path.join(category_path, name)
                            if os.path.isfile(path) and name.endswith(".po"):
                                domain = name[:-3]
                                info = LocaleInfo(
                                    locale, category, domain, path
                                )
                                logger.debug("found: %s", info)
                                yield info

    def has_locale(self, locale_name: str) -> bool:
        """
        Checks if a locale with the given name exists.

        Parameters:
            locale_name: The name of the locale to check.

        Returns:
            bool: True if the locale exists, False otherwise.
        """
        return locale_name in self.locale_names


class GettextCompiler:
    """
    A class used to compile gettext translation files.

    This class is responsible for compiling gettext translation files (.po)
    into binary format (.mo) that can be used by gettext.
    """

    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = cache_dir

    def compile_gettext(self, po_path: str, mo_path: str) -> None:
        """
        Compiles a gettext translation file.

        Parameters:
            po_path: The path to the gettext translation file (.po) to compile.
            mo_path: The path to store the compiled translation file (.mo).
        """
        mofolder = os.path.dirname(mo_path)
        os.makedirs(mofolder, exist_ok=True)
        with open(po_path, encoding="UTF8") as po_file:
            catalog = read_po(po_file)
        with open(mo_path, "wb") as mo_file:
            write_mo(mo_file, catalog)
            logger.debug("writing l18n mo: %s", mo_path)

    def get_mo_path(self, locale: str, category: str, domain: str) -> str:
        """
        Returns the path to the MO file.

        Parameters:
            locale: The locale of the MO file.
            category: The category of the MO file.
            domain: The domain of the MO file.

        Returns:
            The path to the MO file.
            l18n/locale/LC_category/domain_name.mo
        """
        return os.path.join(
            self.cache_dir, LOCALE_DIR, locale, category, domain + ".mo"
        )


class TranslatorPo:
    """
    A class used to translate text using gettext.

    This class is responsible for loading and managing translations, as well as
    providing methods for translating text.
    """

    def __init__(
        self, locale_finder: LocaleFinder, gettext_compiler: GettextCompiler
    ) -> None:
        self.locale_finder = locale_finder
        self.gettext_compiler = gettext_compiler
        self.locale_name: str = prepare.CONFIG.locale
        self.translate: Callable[[str], str] = lambda x: x
        self.language_changed_callbacks: list[Callable[[str], None]] = []

    def collect_languages(self, recompile_translations: bool = False) -> None:
        """
        Collect languages/locales with available translation files.

        Parameters:
            recompile_translations: ``True`` if the translations should be
                recompiled (useful for testing local changes to the
                translations).

        """
        self.build_translations(recompile_translations)
        self.load_translator(self.locale_name)

    def build_translations(self, recompile_translations: bool = False) -> None:
        """
        Create MO files for existing PO translation files.

        Parameters:
            recompile_translations: ``True`` if the translations should be
                recompiled (useful for testing local changes to the
                translations).

        """
        for info in self.locale_finder.search_locales():
            mo_path = self.gettext_compiler.get_mo_path(
                info.locale, info.category, info.domain
            )
            if recompile_translations or not os.path.exists(mo_path):
                self.gettext_compiler.compile_gettext(info.path, mo_path)
                logger.info(f"Built translation file: {mo_path}")
        logger.info("Translation files built successfully")

    def _get_translation(
        self, locale_name: str, domain: str, localedir: str
    ) -> Optional[GNUTranslations]:
        """
        Gets all translators for the given locale and domain.
        """
        for info in self.locale_finder.search_locales():
            if info.locale == locale_name and info.domain == domain:
                return gettext.translation(
                    info.domain, localedir, [locale_name]
                )
        return None

    def load_translator(
        self, locale_name: str = prepare.CONFIG.locale, domain: str = "base"
    ) -> None:
        """
        Load a selected locale for translation.

        Parameters:
            locale_name: Name of the locale.
            domain: Name of the domain.

        """
        logger.debug("loading translator for: %s", locale_name)
        localedir = os.path.join(paths.CACHE_DIR, LOCALE_DIR)
        fallback = gettext.translation("base", localedir, [FALLBACK_LOCALE])
        trans = (
            self._get_translation(locale_name, domain, localedir) or fallback
        )

        if trans is fallback:
            logger.warning("Locale %s not found. Using fallback.", locale_name)

        trans.add_fallback(fallback)
        trans.install()
        self.translate = trans.gettext
        self.locale_name = locale_name

    def get_current_language(self) -> str:
        """
        Returns the current language.

        Returns:
            The current language.
        """
        return self.locale_name

    def is_language_supported(self, locale_name: str) -> bool:
        """
        Checks if a language is supported.

        Parameters:
            locale_name: The name of the language to check.

        Returns:
            True if the language is supported, False otherwise.
        """
        return self.locale_finder.has_locale(locale_name)

    def change_language(self, locale_name: str) -> None:
        """
        Changes the current language to the specified locale.

        Parameters:
            locale_name: The name of the locale to switch to.
        """
        if self.is_language_supported(locale_name):
            self.load_translator(locale_name)
            self.language_changed(locale_name)
        else:
            logger.warning(f"Language {locale_name} is not supported")

    def language_changed(self, locale_name: str) -> None:
        """
        Notifies all registered callbacks that the language has changed.

        Parameters:
            locale_name: The new language.
        """
        if self.is_language_supported(locale_name):
            for callback in self.language_changed_callbacks:
                callback(locale_name)
        else:
            logger.warning(f"Language {locale_name} is not supported")

    def format(
        self,
        text: str,
        parameters: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """
        Replaces variables in a translation string with the given parameters.

        Parameters:
            text: String to format.
            parameters: Parameters to format into the string.

        Returns:
            The formatted string.

        """
        text = text.replace(r"\n", "\n")
        text = self.translate(text)
        if parameters:
            text = text.format(**parameters)
        return text

    def maybe_translate(self, text: Optional[str]) -> str:
        """
        Try to translate the text. If ``None``, return empty string.

        Parameters:
            text: String to translate.

        Returns:
            Translated string.
        """
        if text is None:
            return ""
        else:
            return self.translate(text)


def replace_text(session: Session, text: str) -> str:
    """
    Replaces ``${{var}}`` tiled variables with their in-session value.

    Parameters:
        session: Session containing the information to fill the variables.
        text: Text whose references to variables should be substituted.

    Examples:
        >>> replace_text(session, "${{name}} is running away!")
        'Red is running away!'

    """
    player = session.player
    client = session.client
    unit_measure = player.game_variables.get("unit_measure", prepare.METRIC)

    replacements = {
        "${{name}}": player.name,
        "${{NAME}}": player.name.upper(),
        "${{currency}}": "$",
        "${{money}}": str(player.money.get("player", 0)),
        "${{tuxepedia_seen}}": str(
            sum(
                1
                for status in player.tuxepedia.values()
                if status in (db.SeenStatus.caught, db.SeenStatus.seen)
            )
        ),
        "${{tuxepedia_caught}}": str(
            sum(
                1
                for status in player.tuxepedia.values()
                if status == db.SeenStatus.caught
            )
        ),
        "${{map_name}}": client.map_name,
        "${{map_desc}}": client.map_desc,
        "${{north}}": client.map_north,
        "${{south}}": client.map_south,
        "${{east}}": client.map_east,
        "${{west}}": client.map_west,
    }

    # Add unit-specific replacements
    if unit_measure == prepare.METRIC:
        replacements.update(
            {
                "${{length}}": prepare.U_KM,
                "${{weight}}": prepare.U_KG,
                "${{height}}": prepare.U_CM,
                "${{steps}}": str(convert_km(player.steps)),
            }
        )
    else:
        replacements.update(
            {
                "${{length}}": prepare.U_MI,
                "${{weight}}": prepare.U_LB,
                "${{height}}": prepare.U_FT,
                "${{steps}}": str(convert_mi(player.steps)),
            }
        )

    # Add monster-specific replacements
    for i, monster in enumerate(player.monsters):
        monster_replacements = {
            "${{monster_" + str(i) + "_name}}": monster.name,
            "${{monster_" + str(i) + "_desc}}": monster.description,
            "${{monster_"
            + str(i)
            + "_types}}": " - ".join(
                T.translate(_type.name) for _type in monster.types
            ),
            "${{monster_" + str(i) + "_category}}": monster.category,
            "${{monster_" + str(i) + "_shape}}": T.translate(monster.shape),
            "${{monster_" + str(i) + "_hp}}": str(monster.current_hp),
            "${{monster_" + str(i) + "_hp_max}}": str(monster.hp),
            "${{monster_" + str(i) + "_level}}": str(monster.level),
            "${{monster_"
            + str(i)
            + "_gender}}": T.translate(f"gender_{monster.gender}"),
            "${{monster_" + str(i) + "_bond}}": str(monster.bond),
            "${{monster_" + str(i) + "_txmn_id}}": str(monster.txmn_id),
            "${{monster_"
            + str(i)
            + "_warm}}": T.translate(f"taste_{monster.taste_warm}"),
            "${{monster_"
            + str(i)
            + "_cold}}": T.translate(f"taste_{monster.taste_cold}"),
            "${{monster_"
            + str(i)
            + "_moves}}": " - ".join(_move.name for _move in monster.moves),
        }

        # Add unit-specific monster replacements
        if unit_measure == prepare.METRIC:
            monster_replacements.update(
                {
                    "${{monster_"
                    + str(i)
                    + "_steps}}": str(convert_km(monster.steps)),
                    "${{monster_" + str(i) + "_weight}}": str(monster.weight),
                    "${{monster_" + str(i) + "_height}}": str(monster.height),
                }
            )
        else:
            monster_replacements.update(
                {
                    "${{monster_"
                    + str(i)
                    + "_steps}}": str(convert_mi(monster.steps)),
                    "${{monster_"
                    + str(i)
                    + "_weight}}": str(convert_lbs(monster.weight)),
                    "${{monster_"
                    + str(i)
                    + "_height}}": str(convert_ft(monster.height)),
                }
            )

        monster_replacements.update(
            {
                "${{monster_" + str(i) + "_armour}}": str(monster.armour),
                "${{monster_" + str(i) + "_dodge}}": str(monster.dodge),
                "${{monster_" + str(i) + "_melee}}": str(monster.melee),
                "${{monster_" + str(i) + "_ranged}}": str(monster.ranged),
                "${{monster_" + str(i) + "_speed}}": str(monster.speed),
            }
        )

        replacements.update(monster_replacements)

    # Add game variable replacements
    for key, value in player.game_variables.items():
        replacements.update(
            {
                "${{var:" + str(key) + "}}": str(value),
                "${{msgid:" + str(key) + "}}": T.translate(str(value)),
            }
        )

    # Replace placeholders in the text
    for placeholder, replacement in replacements.items():
        text = text.replace(placeholder, replacement)

    # Replace newline characters
    text = text.replace(r"\n", "\n")

    return text


def process_translate_text(
    session: Session,
    text_slug: str,
    parameters: Iterable[str],
) -> Sequence[str]:
    """
    Translate a dialog to a sequence of pages of text.

    Parameters:
        session: Session containing the information to fill the variables.
        text_slug: Text to translate.
        parameters: A sequence of parameters in the format ``"key=value"`` used
            to format the string.

    """
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


locale_finder = LocaleFinder(prepare.fetch("l18n"))
gettext_compiler = GettextCompiler(paths.CACHE_DIR)
T = TranslatorPo(locale_finder, gettext_compiler)
T.collect_languages()
