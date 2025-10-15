# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

logger = logging.getLogger(__name__)

LOCALE_DIR = "l18n"


class GettextCompiler:
    """
    A class used to compile gettext translation files.

    This class is responsible for compiling gettext translation files (.po)
    into binary format (.mo) that can be used by gettext.
    """

    def __init__(self, cache_dir: Path, locale_dir: str = LOCALE_DIR) -> None:
        self.cache_dir = cache_dir
        self.locale_dir = locale_dir

    def compile_gettext(
        self, po_paths: list[Path], mo_path: Path, locale_name: str
    ) -> None:
        """
        Compiles multiple .po files for the same domain and locale into a
        single .mo file, merging their contents with later files overriding
        earlier ones.
        """
        mofolder = mo_path.parent
        mofolder.mkdir(parents=True, exist_ok=True)

        merged_catalog = Catalog(locale=locale_name)

        for po_path in po_paths:
            try:
                with po_path.open(encoding="UTF8") as po_file:
                    new_catalog = read_po(po_file)
                    merged_catalog.update(new_catalog)
            except Exception as e:
                logger.error(f"Failed to read or merge PO file {po_path}: {e}")

        with mo_path.open("wb") as mo_file:
            write_mo(mo_file, merged_catalog)
            logger.debug(f"Wrote merged MO file: {mo_path}")

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
        return (
            self.cache_dir
            / self.locale_dir
            / locale
            / category
            / f"{domain}.mo"
        )
