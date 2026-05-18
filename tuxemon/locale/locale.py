# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from tuxemon.constants import paths
from tuxemon.constants.asset_loader import (
    fetch_all_l18n_roots,
    fetch_mod_asset_roots,
)
from tuxemon.locale.compiler import GettextCompiler
from tuxemon.locale.finder import LocaleFinder, LocaleInfo
from tuxemon.locale.translator import TranslatorPo
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"
LOCALE_DIR = "l18n"
LOCALE_CONFIG = CONFIG.locale
ONE_WEEK = 7 * 24 * 60 * 60  # seconds


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
        self.clean_stale_translations()
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
            recompile_translations: If True, recompiles MO files even if
                they exist.
        """
        logger.debug("Collecting and compiling translations...")
        self._expected_mo_paths = set()

        for info in self.locale_finder.search_locales():
            mo_path = self.gettext_compiler.get_mo_path(
                info.locale, info.category, info.domain
            )
            self._expected_mo_paths.add(mo_path.resolve())

            if self._should_compile_translation(
                info, mo_path, recompile_translations
            ):
                self.gettext_compiler.compile_gettext(info.path, mo_path)
                logger.info(f"Recompiled .mo for: {mo_path}")

        logger.info("Translation files compilation complete.")

    def _should_compile_translation(
        self, info: LocaleInfo, mo_path: Path, recompile_translations: bool
    ) -> bool:
        try:
            po_mtime = info.path.stat().st_mtime
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Skipping .po file due to error: {e}")
            return False

        try:
            mo_mtime = mo_path.stat().st_mtime if mo_path.exists() else 0
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f".mo stat failed, assuming missing: {e}")
            mo_mtime = 0

        delta = po_mtime - mo_mtime

        if recompile_translations:
            logger.debug(f"Forced recompilation for: {mo_path}")
            return True
        elif not mo_path.exists():
            logger.debug(f".mo file missing, compiling: {mo_path}")
            return True
        elif po_mtime > mo_mtime and delta > ONE_WEEK:
            logger.info(
                f"Recompiled .mo due to freshness gap ({delta:.2f}s): {mo_path}"
            )
            return True
        else:
            logger.debug(
                f"No recompilation needed for: {mo_path} (delta: {delta:.2f}s)"
            )
            return False

    def clean_stale_translations(self) -> None:
        """
        Deletes .mo files that were not generated from any known .po source.
        Ensures no stale or orphaned .mo translation binaries remain.
        """
        logger.debug("Checking for stale .mo files...")

        if not hasattr(self, "_expected_mo_paths"):
            logger.warning(
                "Expected .mo paths not initialized. Skipping cleanup."
            )
            return

        deleted_count = 0
        logger.debug(
            f"Expected .mo paths: {[str(p) for p in self._expected_mo_paths]}"
        )

        for mo_file in self.localedir.rglob("*.mo"):
            logger.debug(f"Checking {mo_file}")
            if not any(mo_file.samefile(p) for p in self._expected_mo_paths):
                logger.info(f"Removing stale .mo: {mo_file}")
                mo_file.unlink()
                deleted_count += 1

        logger.info(
            f"Stale .mo cleanup complete. {deleted_count} files removed."
        )

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

    def _get_translator_for_domain(self, domain: str | None) -> TranslatorPo:
        """
        Returns the appropriate translator based on the domain.
        Falls back to the current translator if domain is None or missing.
        """
        if domain and domain in self._translators:
            return self._translators[domain]
        if domain:
            logger.warning(
                f"Requested domain '{domain}' not found. Using current translator."
            )
        return self.current_translator

    def translate(self, message: str, domain: str | None = None) -> str:
        """
        Translates a message using the currently active translator
        or a specified domain's translator.

        Parameters:
            message: The message string to translate.
            domain: Optional domain to use for translation.
                If None, uses the current translator.

        Returns:
            The translated string.
        """
        return self._get_translator_for_domain(domain).translate(message)

    def format(
        self,
        text: str,
        parameters: Mapping[str, Any] | None = None,
        domain: str | None = None,
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
        return self._get_translator_for_domain(domain).format(text, parameters)

    def maybe_translate(
        self, text: str | None, domain: str | None = None
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

        return self._get_translator_for_domain(domain).maybe_translate(text)

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

            CONFIG.update_attribute("game", "locale", new_locale_name)
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
        return self.locale_finder.get_locale_names()

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
        _locale_mode = CONFIG.locale.translation_mode
        if _locale_mode == "none":
            return
        elif _locale_mode == "all":
            locale_names = self.locale_finder.get_locale_names()
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

    def discover_and_load_all_domains(self, locale_name: str) -> None:
        """
        Discovers all available translation domains and loads a translator for each.

        Parameters:
            locale_name: The locale to use when loading translators.
        """
        logger.info(
            "Discovering and loading all available translation domains..."
        )

        all_domains = {
            info.domain for info in self.locale_finder.search_locales()
        }

        for domain in sorted(all_domains):
            self.load_translator_for_domain(domain, locale_name)

        logger.info(f"Loaded translators for domains: {sorted(all_domains)}")

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


fetch_mod_asset_roots(CONFIG)
all_l18n_mod_paths = fetch_all_l18n_roots()
locale_finder = LocaleFinder(all_l18n_mod_paths)
gettext_compiler = GettextCompiler(paths.CACHE_DIR)
T = TranslatorManager(locale_finder, gettext_compiler)
T.initialize_translations()
T.discover_and_load_all_domains(locale_name=LOCALE_CONFIG.slug)
