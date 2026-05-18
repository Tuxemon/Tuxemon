# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import difflib
import logging
from typing import TYPE_CHECKING

from tuxemon.database.config import DatabaseConfig, EntryNotFoundError

if TYPE_CHECKING:
    from tuxemon.db import DataModel

logger = logging.getLogger(__name__)


class DatabaseQuery:
    """Provides methods for querying the loaded game database."""

    def __init__(
        self,
        database: dict[str, dict[str, DataModel]],
        config: DatabaseConfig,
    ) -> None:
        self._database = database
        self._config = config

    def lookup(self, slug: str, table: str | None = None) -> DataModel:
        """
        Looks up a data model based on slug. Uses default_lookup_table if table is None.
        """
        if table is None:
            table = self._config.default_lookup_table

        table_entry = self._database.get(table)
        if not table_entry:
            raise ValueError(f"Table '{table}' wasn't loaded.")

        if slug not in table_entry:
            self._log_missing_entry_and_raise(table, slug)

        return table_entry[slug]

    def _log_missing_entry_and_raise(self, table: str, slug: str) -> None:
        """Internal helper to log a missing entry and raise EntryNotFoundError."""
        options = difflib.get_close_matches(slug, self._database[table].keys())
        options_str = ", ".join(repr(s) for s in options)
        hint = (
            f"Did you mean {options_str}?"
            if options
            else "No similar slugs found."
        )
        raise EntryNotFoundError(
            f"Lookup failed for unknown {table} '{slug}'. {hint}"
        )

    def get_entry(self, table: str, slug: str) -> str:
        """
        Checks existence of an entry and returns its file path/slug.
        NOTE: Since 'file' is not a guaranteed attribute on DataModel,
        this implementation returns 'slug' as a fallback if 'file' isn't
        present.
        """
        table_data = self._database.get(table)

        if not table_data:
            raise ValueError(
                f"Table '{table}' does not exist in the database."
            )

        entry = table_data.get(slug)

        if entry is None:
            raise EntryNotFoundError(
                f"Entry '{slug}' not found in table '{table}'."
            )

        # Assuming DataModel has a 'file' attribute or slug as a fallback
        return getattr(entry, "file", slug)

    @property
    def all_data(self) -> dict[str, dict[str, DataModel]]:
        """Provides read-only access to the loaded database."""
        return self._database
