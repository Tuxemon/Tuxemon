# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, UnidentifiedImageError

from tuxemon.constants.asset_loader import (
    fetch_asset,
)
from tuxemon.locale.locale import T
from tuxemon.platform.const.sizes import NATIVE_RESOLUTION

if TYPE_CHECKING:
    from tuxemon.database.data import ModData


class Validator:
    """
    Helper class for validating resources exist.
    """

    def __init__(self, database: ModData) -> None:
        self.db = database
        self.db.preload()

    def translation(self, msgid: str) -> bool:
        """
        Check to see if a translation exists for the given slug

        Parameters:
            msgid: The slug of the text to translate. A short English
                identifier.

        Returns:
            True if translation exists
        """
        translated_text = T.translate(msgid)
        return translated_text not in (msgid, "")

    def file(self, file: str) -> bool:
        """
        Check to see if a given file exists

        Parameters:
            file: The file path relative to a mod directory

        Returns:
            True if file exists
        """
        try:
            path = Path(fetch_asset(file))
            return path.exists()
        except OSError:
            return False

    def size(self, file: str, size: tuple[int, int]) -> bool:
        """
        Check to see if a given file respects the predefined size.

        Parameters:
            file: The file path relative to a mod directory
            size: The predefined size

        Returns:
            True if file respects
        """
        try:
            path = fetch_asset(file)
            with Image.open(path) as sprite:
                native = NATIVE_RESOLUTION
                if size == native:
                    if sprite.size[0] > size[0] or sprite.size[1] > size[1]:
                        return False
                else:
                    if sprite.size != size:
                        return False
            return True
        except (OSError, FileNotFoundError, UnidentifiedImageError):
            return False

    def db_entry(self, table: str, slug: str) -> bool:
        """
        Check to see if the given slug exists in the database for the given
        table.

        Parameters:
            slug: The slug of the monster, technique, item, or npc.  A short
                English identifier.
            table: Which index to do the search in. Can be: "monster",
                "item", "npc", or "technique".

        Returns:
            True if entry exists
        """
        return slug in self.db._preloaded.get(table, {})
