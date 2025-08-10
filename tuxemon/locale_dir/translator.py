# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import gettext
import logging
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"


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
