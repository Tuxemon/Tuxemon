# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


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

    This class searches for locales in the specified directories and provides
    access to locale metadata via scanning, querying, and caching.
    """

    def __init__(self, root_dirs: list[Path], auto_scan: bool = False) -> None:
        self.root_dirs = tuple(root_dirs)
        self._locale_names: set[str] = set()
        self._locale_infos: list[LocaleInfo] = []
        self._scanned: bool = False

        if auto_scan:
            self._scan()

    def _scan(self) -> None:
        logger.debug("Scanning locales across multiple root directories...")
        for root_dir in self.root_dirs:
            if not root_dir.is_dir():
                logger.warning(
                    f"Locale root directory not found or not a directory: {root_dir}"
                )
                continue

            for locale_path in root_dir.iterdir():
                if locale_path.is_dir():
                    self._locale_names.add(locale_path.name)
                    for category_path in locale_path.iterdir():
                        if category_path.is_dir():
                            for file_path in category_path.iterdir():
                                if (
                                    file_path.is_file()
                                    and file_path.suffix == ".po"
                                ):
                                    domain = file_path.stem
                                    info = LocaleInfo(
                                        locale=locale_path.name,
                                        category=category_path.name,
                                        domain=domain,
                                        path=file_path,
                                    )
                                    self._locale_infos.append(info)
                                    logger.debug(
                                        f"Found: {info} in root: {root_dir}"
                                    )
        self._scanned = True

    def search_locales(self) -> Generator[LocaleInfo, None, None]:
        """
        Yields all discovered LocaleInfo objects.
        Automatically triggers a scan if not already done.
        """
        if not self._scanned:
            self._scan()
        yield from self._locale_infos

    def has_locale(self, locale_name: str) -> bool:
        """
        Checks if a locale with the given name exists.
        """
        if not self._scanned:
            logger.warning(
                "LocaleFinder hasn't scanned directories yet. Triggering scan now."
            )
            self._scan()
        return locale_name in self._locale_names

    def reset(self) -> None:
        """
        Clears all cached locale information and allows rescanning.
        """
        logger.info("Resetting LocaleFinder scan state and caches.")
        self._locale_names.clear()
        self._locale_infos.clear()
        self._scanned = False

    def get_locales(self) -> list[LocaleInfo]:
        """
        Returns all discovered locales as a list.
        """
        if not self._scanned:
            self._scan()
        return self._locale_infos.copy()

    def get_locale_names(self) -> list[str]:
        """
        Returns a sorted list of locale names discovered by LocaleFinder.
        Triggers a scan if it hasn't run yet.
        """
        if not self._scanned:
            self._scan()
        return sorted(self._locale_names)
