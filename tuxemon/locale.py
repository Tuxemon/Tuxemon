# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import gettext
import logging
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from tuxemon import prepare
from tuxemon.constants import paths

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


class TranslatorManager:
    """
    Manages multiple Translator instances, allowing for different translation
    contexts (e.g., base game, mods). It handles compilation of PO files
    and provides an interface for dynamic language switching and domain management.
    """

    def __init__(
        self, locale_finder: LocaleFinder, gettext_compiler: GettextCompiler
    ) -> None:
        self.locale_finder = locale_finder
        self.gettext_compiler = gettext_compiler
        self.localedir = paths.L18N_MO_FILES
        self._translators: dict[str, TranslatorPo] = {}
        self._current_translator_key: str = "base"
        self.language_changed_callbacks: list[Callable[[str], None]] = []
        self.collect_and_compile_translations()
        self.load_translator_for_domain(
            self._current_translator_key, LOCALE_CONFIG.slug
        )

    def collect_and_compile_translations(
        self, recompile_translations: bool = False
    ) -> None:
        """
        Collects available translation files using the LocaleFinder and
        compiles them into MO files using the GettextCompiler.

        Parameters:
            recompile_translations: If True, recompiles MO files even
                if they exist.
        """
        logger.debug("Collecting and compiling translations...")
        for info in self.locale_finder.search_locales():
            mo_path = self.gettext_compiler.get_mo_path(
                info.locale, info.category, info.domain
            )
            if recompile_translations or not mo_path.exists():
                self.gettext_compiler.compile_gettext(info.path, mo_path)
                logger.info(f"Built translation file: {mo_path}")
        logger.info("Translation files compilation complete.")

    def load_translator_for_domain(
        self, domain: str, locale_name: str
    ) -> None:
        """
        Loads or reloads a Translator instance for a specific domain and locale.
        This method ensures that a Translator exists for the given domain.

        Parameters:
            domain: The translation domain (e.g., "base", "my_mod_id").
            locale_name: The locale to load for this domain.
        """
        if not self.locale_finder.has_locale(locale_name):
            logger.warning(
                f"Requested locale '{locale_name}' not found for domain '{domain}'. Using fallback '{FALLBACK_LOCALE}'."
            )
            actual_locale_name = FALLBACK_LOCALE
        else:
            actual_locale_name = locale_name

        self._translators[domain] = TranslatorPo(
            locale_name=actual_locale_name,
            domain=domain,
            localedir=self.localedir,
            fallback_locale=FALLBACK_LOCALE,
        )
        logger.debug(
            f"Translator for domain '{domain}' loaded/reloaded with locale '{actual_locale_name}'."
        )

    def set_current_translator(self, domain: str) -> None:
        """
        Sets the active translator based on the provided domain.
        Subsequent calls to `translate()` (without a domain override)
        will use this translator.

        Parameters:
            domain: The domain of the translator to make active.
        """
        if domain not in self._translators:
            logger.warning(
                f"Translator for domain '{domain}' is not loaded. "
                f"Falling back to the 'base' domain translator."
            )
            self._current_translator_key = "base"
            if "base" not in self._translators:
                self.load_translator_for_domain("base", LOCALE_CONFIG.slug)
        else:
            self._current_translator_key = domain
        logger.debug(
            f"Current translator set to domain: '{self._current_translator_key}'"
        )

    @property
    def current_translator(self) -> TranslatorPo:
        """
        Returns the currently active Translator instance.
        """
        return self._translators[self._current_translator_key]

    def translate(self, message: str) -> str:
        """
        Translates a message using the currently active translator.
        This is the primary method for simple text translation.

        Parameters:
            message: The message string to translate.

        Returns:
            The translated string.
        """
        return self.current_translator.translate(message)

    def format(
        self,
        text: str,
        parameters: Optional[Mapping[str, Any]] = None,
        domain: Optional[str] = None,
    ) -> str:
        """
        Replaces variables in a translation string with the given parameters,
        using either the current translator or a specified domain's translator.

        Parameters:
            text: String to format.
            parameters: Parameters to format into the string.
            domain: Optional domain to use for translation.
                If None, uses the current translator.

        Returns:
            The formatted string.
        """
        target_translator = self.current_translator
        if domain and domain in self._translators:
            target_translator = self._translators[domain]
        elif domain:
            logger.warning(
                f"Requested domain '{domain}' not found for formatting. Using current translator."
            )

        return target_translator.format(text, parameters)

    def maybe_translate(
        self, text: Optional[str], domain: Optional[str] = None
    ) -> str:
        """
        Try to translate the text. If ``None``, return empty string.
        Allows specifying a domain for translation.

        Parameters:
            text: String to translate.
            domain: Optional domain to use for translation.
                If None, uses the current translator.

        Returns:
            Translated string.
        """
        if text is None:
            return ""

        target_translator = self.current_translator
        if domain and domain in self._translators:
            target_translator = self._translators[domain]
        elif domain:
            logger.warning(
                f"Requested domain '{domain}' not found for maybe_translate."
                " Using current translator."
            )

        return target_translator.maybe_translate(text)

    def get_current_language(self) -> str:
        """
        Returns the locale of the currently active translator.

        Returns:
            The current language slug (e.g., "en_US").
        """
        return self.current_translator.locale_name

    def is_language_supported(self, locale_name: str) -> bool:
        """
        Checks if a language (locale) is supported by checking with
        the LocaleFinder.

        Parameters:
            locale_name: The name of the locale to check.

        Returns:
            True if the locale exists in the discovered paths, False
            otherwise.
        """
        return self.locale_finder.has_locale(locale_name)

    def change_language(self, new_locale_name: str) -> None:
        """
        Changes the language for all currently loaded translator domains.
        This reloads each active translator with the new locale.

        Parameters:
            new_locale_name: The name of the locale to switch to (e.g., "fr_FR").
        """
        if self.is_language_supported(new_locale_name):
            domains_to_reload = list(self._translators.keys())
            for domain in domains_to_reload:
                self.load_translator_for_domain(domain, new_locale_name)

            LOCALE_CONFIG.slug = new_locale_name
            logger.info(f"Language changed globally to: {new_locale_name}")
            self.invoke_language_changed_callbacks(new_locale_name)
        else:
            logger.warning(
                f"Language '{new_locale_name}' is not supported. Language not changed."
            )

    def get_available_languages(self) -> list[str]:
        """
        Returns a sorted list of all available language slugs found by
        the LocaleFinder.
        """
        return sorted(list(self.locale_finder.locale_names))

    def invoke_language_changed_callbacks(self, locale_name: str) -> None:
        """
        Notifies all registered callbacks that the language has changed.
        This method is called internally by `change_language`.

        Parameters:
            locale_name: The new language slug.
        """
        for callback in self.language_changed_callbacks:
            try:
                callback(locale_name)
            except Exception as e:
                logger.error(
                    f"Error in language change callback for locale '{locale_name}': {e}",
                    exc_info=True,
                )

    def has_translation(
        self, locale_name: str, msgid: str, domain: str = "base"
    ) -> bool:
        """
        Checks if a translation exists for a certain language and message ID
        within a specific domain. This method is useful for development checks.

        Parameters:
            locale_name: The name of the language (locale) to check.
            msgid: The msgid (original string) of the translation to check.
            domain: The domain (e.g., "base", "my_mod") to check for the
                translation.

        Returns:
            True if the translation exists, False otherwise.
        """
        if (
            domain in self._translators
            and self._translators[domain].locale_name == locale_name
        ):
            return self._translators[domain].has_translation(msgid)
        else:
            try:
                temp_translator = TranslatorPo(
                    locale_name, domain, self.localedir, FALLBACK_LOCALE
                )
                return temp_translator.has_translation(msgid)
            except Exception as e:
                logger.debug(
                    f"Could not create temporary translator for check"
                    f"(locale='{locale_name}', domain='{domain}'): {e}"
                )
                return False

    def _log_missing_translation(
        self, locale_name: str, msgid: str, domain: str = "base"
    ) -> None:
        """
        Logs an error when a translation for the given msgid is missing
        for a specific locale and domain.
        """
        logger.error(
            f"Missing translation in domain '{domain}' for locale '{locale_name}': '{msgid}'"
        )

    def check_translation(self, message_id: str, domain: str = "base") -> None:
        """
        Checks if a translation exists for a certain message_id in the
        specified locale(s) for a given domain, based on the global
        `translation_mode` configuration.

        Parameters:
            message_id: The message_id of the translation to check.
            domain: The domain to check for the translation
                (e.g., "base", "my_mod").
        """
        _locale_mode = prepare.CONFIG.locale.translation_mode
        if _locale_mode == "none":
            return
        elif _locale_mode == "all":
            locale_names = self.locale_finder.locale_names.copy()
            if "README.md" in locale_names:
                locale_names.remove("README.md")

            for locale_name in locale_names:
                if (
                    locale_name
                    and message_id
                    and not self.has_translation(
                        locale_name, message_id, domain
                    )
                ):
                    self._log_missing_translation(
                        locale_name, message_id, domain
                    )
        else:
            if self.is_language_supported(_locale_mode):
                if not self.has_translation(_locale_mode, message_id, domain):
                    self._log_missing_translation(
                        _locale_mode, message_id, domain
                    )
            else:
                raise ValueError(
                    f"Configured locale mode '{_locale_mode}' doesn't exist as a supported language."
                )

    def initialize_translations(
        self,
        locale_name: str = LOCALE_CONFIG.slug,
        domain: str = "base",
        recompile: bool = False,
    ) -> None:
        """
        Compiles translation files and loads the translator for the
        specified domain and locale.

        Parameters:
            locale_name: The target locale (e.g., "de_DE", "fr_FR").
            domain: The domain to load (e.g., "base", "ui").
            recompile: Whether to force recompilation of translation files.
        """
        self.collect_and_compile_translations(recompile_translations=recompile)
        self.load_translator_for_domain(domain, locale_name)
        logger.info(
            f"Initialized translator for domain '{domain}', locale '{locale_name}'"
        )


class TranslatorPo:
    """
    A class used to translate text using a specific gettext translation
    instance. This class handles the core logic of text translation and
    caching for a given locale and domain.
    """

    def __init__(
        self,
        locale_name: str,
        domain: str,
        localedir: Path,
        fallback_locale: str = FALLBACK_LOCALE,
    ) -> None:
        self.locale_name = locale_name
        self.domain = domain
        self.localedir = localedir
        self.fallback_locale = fallback_locale
        self._translation_cache: dict[str, str] = {}
        self._real_translate: Callable[[str], str] = (
            self._load_gettext_translation()
        )
        self.translate: Callable[[str], str] = self._translate_with_cache

    def _load_gettext_translation(self) -> Callable[[str], str]:
        """
        Loads and returns the gettext translation function for this translator.
        Handles fallback if the specific translation is not found.
        """
        trans: Union[gettext.GNUTranslations, gettext.NullTranslations]
        try:
            trans = gettext.translation(
                self.domain, self.localedir, [self.locale_name]
            )
            logger.debug(
                f"Loaded translation for domain '{self.domain}', locale '{self.locale_name}'"
            )
        except FileNotFoundError:
            logger.warning(
                f"Translation file not found for domain '{self.domain}',"
                f"locale '{self.locale_name}'. "
                f"Attempting to use fallback '{self.fallback_locale}'."
            )
            try:
                trans = gettext.translation(
                    self.domain, self.localedir, [self.fallback_locale]
                )
                logger.debug(
                    f"Loaded fallback translation for domain '{self.domain}',"
                    f"locale '{self.fallback_locale}'"
                )
            except FileNotFoundError:
                logger.error(
                    f"No translation found for domain '{self.domain}' in any locale."
                    " Using NullTranslations."
                )
                trans = gettext.NullTranslations()

        try:
            fallback_base_trans = gettext.translation(
                "base", self.localedir, [self.fallback_locale]
            )
            trans.add_fallback(fallback_base_trans)
            logger.debug(
                f"Added 'base' domain fallback translation for locale '{self.fallback_locale}'"
            )
        except FileNotFoundError:
            logger.error(
                f"Base fallback translation 'base' for locale '{self.fallback_locale}' not found."
                "Translations might be very incomplete."
            )

        return trans.gettext

    def _translate_with_cache(self, message: str) -> str:
        """Translates a message, caching the result."""
        if message in self._translation_cache:
            return self._translation_cache[message]

        translated_message = self._real_translate(message)
        self._translation_cache[message] = translated_message
        return translated_message

    def get_current_language(self) -> str:
        """
        Returns the locale name this translator is configured for.

        Returns:
            The current language.
        """
        return self.locale_name

    def has_translation(self, msgid: str) -> bool:
        """
        Checks if a translation exists for a given message ID within this
        translator's context.

        Parameters:
            msgid: The msgid of the translation to check.

        Returns:
            True if the translation exists, False otherwise.
        """
        return self._real_translate(msgid) != msgid

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


locale_finder = LocaleFinder(Path(prepare.fetch("l18n")))
gettext_compiler = GettextCompiler(paths.CACHE_DIR)
T = TranslatorManager(locale_finder, gettext_compiler)
T.initialize_translations()
