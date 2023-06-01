# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import dataclasses
import gettext
import logging
import os
import os.path
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    Mapping,
    Optional,
    Sequence,
)

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from tuxemon import formula, prepare
from tuxemon.constants import paths
from tuxemon.session import Session

logger = logging.getLogger(__name__)

FALLBACK_LOCALE = "en_US"


@dataclasses.dataclass(frozen=True, order=True)
class LocaleInfo:
    """Information about a locale."""

    locale: str
    category: str
    domain: str
    path: str


class TranslatorPo:
    """
    gettext-based translator class.

    po files are read and compiled into mo files by gettext.
    the mo files are saved in ~/.tuxemon/cache/l18n.

    """

    def __init__(self) -> None:
        self.translate: Callable[[str], str] = lambda x: x

    @staticmethod
    def search_locales() -> Generator[LocaleInfo, None, None]:
        """
        Search local folder and return LocaleInfo objects.

        Yields:
            The information of each locale.

        """
        logger.debug("searching locales...")
        root = prepare.fetch("l18n")
        for locale in os.listdir(root):
            locale_path = os.path.join(root, locale)
            if os.path.isdir(locale_path):
                for category in os.listdir(locale_path):
                    category_path = os.path.join(locale_path, category)
                    if os.path.isdir(category_path):
                        for name in os.listdir(category_path):
                            path = os.path.join(category_path, name)
                            if os.path.isfile(path) and name.endswith(".po"):
                                domain = name[:-3]
                                info = LocaleInfo(
                                    locale,
                                    category,
                                    domain,
                                    path,
                                )
                                logger.debug("found: %s", info)
                                yield info

    def collect_languages(self, recompile_translations: bool = False) -> None:
        """
        Collect languages/locales with available translation files.

        Parameters:
            recompile_translations: ``True`` if the translations should be
                recompiled (useful for testing local changes to the
                translations).

        """
        self.build_translations(recompile_translations)
        self.load_translator(prepare.CONFIG.locale)

    def build_translations(self, recompile_translations: bool = False) -> None:
        """
        Create MO files for existing PO translation files.

        Parameters:
            recompile_translations: ``True`` if the translations should be
                recompiled (useful for testing local changes to the
                translations).

        """
        # l18n/locale/LC_category/domain_name.mo
        cache = os.path.join(paths.CACHE_DIR, "l18n")
        for info in self.search_locales():
            mo_path = os.path.join(
                cache,
                info.locale,
                info.category,
                info.domain + ".mo",
            )
            if recompile_translations or not os.path.exists(mo_path):
                self.compile_gettext(info.path, mo_path)

    @staticmethod
    def compile_gettext(po_path: str, mo_path: str) -> None:
        """
        Compile po file into mo file.

        Parameters:
            po_path: Path of the po file.
            mo_path: Path of the mo file.

        """
        mofolder = os.path.dirname(mo_path)
        os.makedirs(mofolder, exist_ok=True)
        with open(po_path, encoding="UTF8") as po_file:
            catalog = read_po(po_file)
        with open(mo_path, "wb") as mo_file:
            write_mo(mo_file, catalog)
            logger.debug("writing l18n mo: %s", mo_path)

    def load_translator(
        self,
        locale_name: str = "en_US",
        domain: str = "base",
    ) -> None:
        """
        Load a selected locale for translation.

        Parameters:
            locale_name: Name of the locale.
            domain: Name of the domain.

        """
        logger.debug("loading translator for: %s", locale_name)
        localedir = os.path.join(paths.CACHE_DIR, "l18n")
        fallback = gettext.translation("base", localedir, [FALLBACK_LOCALE])

        for info in self.search_locales():
            if info.locale == locale_name and info.domain == domain:
                trans = gettext.translation(
                    info.domain,
                    localedir,
                    [locale_name],
                )
                trans.add_fallback(fallback)
                break
        else:
            logger.warning("Locale %s not found. Using fallback.", locale_name)
            trans = fallback
        trans.install()
        self.translate = trans.gettext

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
    text = text.replace("${{name}}", player.name)
    text = text.replace("${{currency}}", "$")
    text = text.replace(r"\n", "\n")
    text = text.replace("${{money}}", str(player.money["player"]))
    # distance (metric / imperial)
    if player.game_variables["unit_measure"] == "Metric":
        text = text.replace("${{length}}", "km")
        text = text.replace("${{weight}}", "kg")
        text = text.replace("${{height}}", "cm")
        text = text.replace(
            "${{steps}}",
            str(formula.convert_km(player.game_variables["steps"])),
        )
    else:
        text = text.replace("${{length}}", "mi")
        text = text.replace("${{weight}}", "lb")
        text = text.replace("${{height}}", "ft")
        text = text.replace(
            "${{steps}}",
            str(formula.convert_mi(player.game_variables["steps"])),
        )
    # maps
    text = text.replace("${{map_name}}", client.map_name)
    text = text.replace("${{map_desc}}", client.map_desc)
    text = text.replace("${{north}}", client.map_north)
    text = text.replace("${{south}}", client.map_south)
    text = text.replace("${{east}}", client.map_east)
    text = text.replace("${{west}}", client.map_west)

    for i in range(len(player.monsters)):
        monster = player.monsters[i]
        text = text.replace("${{monster_" + str(i) + "_name}}", monster.name)
        text = text.replace(
            "${{monster_" + str(i) + "_desc}}",
            monster.description,
        )
        text = text.replace("${{monster_" + str(i) + "_type}}", monster.slug)
        text = text.replace(
            "${{monster_" + str(i) + "_category}}",
            monster.category,
        )
        text = text.replace("${{monster_" + str(i) + "_shape}}", monster.shape)
        text = text.replace(
            "${{monster_" + str(i) + "_hp}}",
            str(monster.current_hp),
        )
        text = text.replace(
            "${{monster_" + str(i) + "_hp_max}}",
            str(monster.hp),
        )
        text = text.replace(
            "${{monster_" + str(i) + "_level}}",
            str(monster.level),
        )

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


T = TranslatorPo()
