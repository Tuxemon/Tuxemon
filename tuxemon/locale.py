# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import gettext
import logging
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from gettext import GNUTranslations
from pathlib import Path
from typing import Any, Optional

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from tuxemon import prepare
from tuxemon.constants import paths
from tuxemon.constants.asset_loader import fetch_asset, fetch_mod_asset_roots

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"
LOCALE_DIR = "l18n"
LOCALE_CONFIG = prepare.CONFIG.locale


@dataclass(frozen=True, order=True)
class LocaleInfo:
    """Information about a locale."""

    locale: str
    category: str
    domain: str
    path: Path


class LocaleFinder:
    """
    A class used to find and manage locales.

    This class is responsible for searching for locales in a given directory
    and providing information about the found locales.
    """

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.locale_names: set[str] = set()

    def search_locales(self) -> Generator[LocaleInfo, Any, None]:
        """
        Searches for locales in the given directory.

        Yields:
            LocaleInfo: Information about each found locale.
        """
        logger.debug("searching locales...")
        for locale_path in self.root_dir.iterdir():
            if locale_path.is_dir():
                self.locale_names.add(locale_path.name)
                for category_path in locale_path.iterdir():
                    if category_path.is_dir():
                        for file_path in category_path.iterdir():
                            if (
                                file_path.is_file()
                                and file_path.suffix == ".po"
                            ):
                                domain = file_path.stem
                                info = LocaleInfo(
                                    locale_path.name,
                                    category_path.name,
                                    domain,
                                    file_path,
                                )
                                logger.debug(f"Found: {info}")
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

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    def compile_gettext(self, po_path: Path, mo_path: Path) -> None:
        """
        Compiles a gettext translation file.

        Parameters:
            po_path: The path to the gettext translation file (.po) to compile.
            mo_path: The path to store the compiled translation file (.mo).
        """
        mofolder = mo_path.parent
        mofolder.mkdir(parents=True, exist_ok=True)

        with po_path.open(encoding="UTF8") as po_file:
            catalog = read_po(po_file)

        with mo_path.open("wb") as mo_file:
            write_mo(mo_file, catalog)
            logger.debug(f"writing l18n mo: {mo_path}")

    def get_mo_path(self, locale: str, category: str, domain: str) -> Path:
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
        return self.cache_dir / LOCALE_DIR / locale / category / f"{domain}.mo"


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
        self.locale_name: str = LOCALE_CONFIG.slug
        self.translate: Callable[[str], str] = self._translate_with_cache
        self.language_changed_callbacks: list[Callable[[str], None]] = []
        self._translation_cache: dict[str, str] = {}
        self.collect_languages()

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
            if recompile_translations or not mo_path.exists():
                self.gettext_compiler.compile_gettext(info.path, mo_path)
                logger.info(f"Built translation file: {mo_path}")
        logger.info("Translation files built successfully")

    def _get_translation(
        self, locale_name: str, domain: str, localedir: Path
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
        self, locale_name: str = LOCALE_CONFIG.slug, domain: str = "base"
    ) -> None:
        """
        Load a selected locale for translation.

        Parameters:
            locale_name: Name of the locale.
            domain: Name of the domain.
        """
        logger.debug(f"loading translator for: {locale_name}")
        localedir = paths.L18N_MO_FILES
        fallback = gettext.translation("base", localedir, [FALLBACK_LOCALE])
        trans = (
            self._get_translation(locale_name, domain, localedir) or fallback
        )

        if trans is fallback:
            logger.warning(f"Locale {locale_name} not found. Using fallback.")

        trans.add_fallback(fallback)
        self._set_translate_function(trans.gettext)
        self.locale_name = locale_name

    def _set_translate_function(
        self, translate_func: Callable[[str], str]
    ) -> None:
        """Sets the internal translation function and clears the cache."""
        self._real_translate = translate_func
        self._translation_cache.clear()

    def _translate_with_cache(self, message: str) -> str:
        """Translates a message, caching the result."""
        if message in self._translation_cache:
            return self._translation_cache[message]

        translated_message = self._real_translate(message)
        self._translation_cache[message] = translated_message
        return translated_message

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

    def get_available_languages(self) -> list[str]:
        """
        Returns a list of all available languages.
        """
        return sorted(list(self.locale_finder.locale_names))

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

    def has_translation(self, locale_name: str, msgid: str) -> bool:
        """
        Checks if a translation exists for a certain language.

        Parameters:
            locale_name: The name of the language to check.
            msgid: The msgid of the translation to check.

        Returns:
            True if the translation exists, False otherwise.
        """
        localedir = paths.L18N_MO_FILES
        trans = self._get_translation(locale_name, "base", localedir)
        if trans is None:
            return False
        return trans.gettext(msgid) != msgid

    def _log_missing_translation(self, locale_name: str, msgid: str) -> None:
        """
        Logs an error when a translation for the given msgid is missing
        for a specific locale.
        """
        logger.error(f"Translation doesn't exist for '{locale_name}': {msgid}")

    def check_translation(self, message_id: str) -> None:
        """
        Checks if a translation exists for a certain message_id in all existing locales.

        Parameters:
            message_id: The message_id of the translation to check.
        """
        _locale = prepare.CONFIG.locale.translation_mode
        if _locale == "none":
            return
        else:
            if _locale == "all":
                locale_names = self.locale_finder.locale_names.copy()
                locale_names.remove("README.md")
                for locale_name in locale_names:
                    if (
                        locale_name
                        and message_id
                        and not self.has_translation(locale_name, message_id)
                    ):
                        self._log_missing_translation(locale_name, message_id)
            else:
                if self.is_language_supported(_locale):
                    if not self.has_translation(_locale, message_id):
                        self._log_missing_translation(_locale, message_id)
                else:
                    raise ValueError(f"Locale '{_locale}' doesn't exist.")

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


fetch_mod_asset_roots(prepare.CONFIG)
locale_finder = LocaleFinder(Path(fetch_asset("l18n")))
gettext_compiler = GettextCompiler(paths.CACHE_DIR)
T = TranslatorPo(locale_finder, gettext_compiler)
T.collect_languages()
