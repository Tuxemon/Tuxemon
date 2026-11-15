# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path

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
            logger.debug(f"writing {self.locale_dir} mo: {mo_path}")

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
