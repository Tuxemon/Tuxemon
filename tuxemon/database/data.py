# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from tuxemon.database.config import DatabaseConfig
from tuxemon.database.loader import ModelLoader, load_files
from tuxemon.database.management import (
    DependencyResolver,
    ModMetadataLoader,
    ModMetadataManager,
)
from tuxemon.database.query import DatabaseQuery

if TYPE_CHECKING:
    from tuxemon.db import DataModel

logger = logging.getLogger(__name__)


class ModData:
    """
    Core manager for loading, storing, and accessing game data from mods.
    Acts as the orchestrator for loading, validation, and dependency resolution.
    """

    def __init__(
        self,
        config: DatabaseConfig,
        loader: ModelLoader,
    ) -> None:
        self._config = config
        self._loader = loader
        self._resolver = DependencyResolver(config.mod_dependencies)

        self._preloaded: dict[str, dict[str, Any]] = {}
        self._database: dict[str, dict[str, DataModel]] = {}

        mod_loader = ModMetadataLoader(
            config.active_mods, config.mod_base_path
        )
        self._mod_manager = ModMetadataManager(mod_loader.load_metadata())
        self._query_manager = DatabaseQuery(self._database, self._config)

        if self._config.mod_tables:
            for mod, tables in self._config.mod_tables.items():
                if mod in self._config.active_mods:
                    for table in tables:
                        self._preloaded.setdefault(table, {})
                        self._database.setdefault(table, {})

    @property
    def database(self) -> dict[str, dict[str, DataModel]]:
        """Read-only access to the loaded database."""
        return self._query_manager.all_data

    @property
    def mod_metadata(self) -> ModMetadataManager:
        """Access to the Mod Metadata Manager for queries."""
        return self._mod_manager

    def lookup(self, slug: str, table: str | None = None) -> DataModel:
        """Looks up a data model based on slug."""
        return self._query_manager.lookup(slug, table)

    def get_entry(self, table: str, slug: str) -> str:
        """Checks existence of an entry and returns its file path/slug."""
        return self._query_manager.get_entry(table, slug)

    def preload(self, directory: str = "all") -> None:
        """Loads all data from JSON/YAML files into the untyped preloaded dictionary."""
        if directory == "all":
            if not self._config.mod_tables:
                logger.warning("No mod tables specified in config.")
                return

            active_table_mods = [
                mod
                for mod in self._config.active_mods
                if mod in self._config.mod_tables
            ]

            # Determine load order based on dependencies
            ordered_mods_for_loading = []
            resolved_set = set()

            for mod in active_table_mods:
                dependencies = self._resolver.resolve(mod)

                for dep in dependencies:
                    if dep not in resolved_set and dep in active_table_mods:
                        ordered_mods_for_loading.append(dep)
                        resolved_set.add(dep)

                if mod not in resolved_set:
                    ordered_mods_for_loading.append(mod)
                    resolved_set.add(mod)

            logger.info(
                f"Final ordered mods for loading: {ordered_mods_for_loading}"
            )

            for mod_to_load in ordered_mods_for_loading:
                if mod_to_load in self._config.mod_tables:
                    logger.info(f"Preloading mod: {mod_to_load}")
                    for table in self._config.mod_tables[mod_to_load]:
                        self._preload_table(table, mod_to_load)
        else:
            self._preload_table(directory, None)

    def _preload_table(
        self, table: str, mod_directory: str | None = None
    ) -> None:
        """Internal helper to preload table data from mod directories."""
        mod_directories = (
            [mod_directory] if mod_directory else self._get_truly_active_mods()
        )

        for mod_dir in mod_directories:
            if (
                self._config.mod_table_exclusions
                and mod_dir in self._config.mod_table_exclusions
                and table in self._config.mod_table_exclusions[mod_dir]
            ):
                logger.info(f"Table '{table}' excluded by mod '{mod_dir}'.")
                continue

            base_path = (
                Path(self._config.mod_base_path)
                / mod_dir
                / self._config.mod_db_subfolder
            )
            db_path = base_path / table

            if db_path.exists():
                logger.debug(f"Loading table '{table}' from '{db_path}'.")
                data_loader = load_files(table, base_path, self._config)
                # Overwrites happen inside load_files/load_dict based on mod load order
                self._preloaded.setdefault(table, {}).update(data_loader)
            else:
                logger.debug(
                    f"Database directory '{db_path}' not found. Skipping."
                )

    def _get_truly_active_mods(self) -> list[str]:
        """Returns the list of active mods that are not deactivated via mod_activation."""
        return [
            mod
            for mod in self._config.active_mods
            if self._config.mod_activation.get(mod, True)
        ]

    def load(self, directory: str = "all", validate: bool = True) -> None:
        """Loads all preloaded raw data into validated DataModels in the database."""
        if directory == "all":
            if self._config.mod_tables:
                for mod, tables in self._config.mod_tables.items():
                    if mod in self._config.active_mods:
                        for table in tables:
                            self._load_models_from_preloaded(table, validate)
            else:
                logger.debug("No mod tables specified in config.")
        else:
            self._load_models_from_preloaded(directory, validate)

    def _load_models_from_preloaded(self, table: str, validate: bool) -> None:
        """Internal helper to load models from preloaded data into the main database."""
        if table not in self._preloaded:
            logger.warning(
                f"Attempted to load models for table '{table}' which was not preloaded."
            )
            return

        for item in self._preloaded[table].values():
            item_copy = dict(item)
            # Remove internal paths key before validation/loading
            if "paths" in item_copy:
                del item_copy["paths"]

            model = self._validate_and_load(item_copy, table, validate)
            if model:
                self._database[table][model.slug] = model

    def _validate_and_load(
        self, item: Mapping[str, Any], table: str, validate: bool
    ) -> DataModel | None:
        """Internal helper to validate and load a model entry via ModelLoader."""
        try:
            # ModelLoader is responsible for logging ValidationError exceptions
            return self._loader.load(item, table, validate=validate)
        except ValidationError as e:
            if validate:
                raise e
            return None
        except RuntimeError:
            return None

    def load_model(
        self, item: Mapping[str, Any], table: str, validate: bool = False
    ) -> None:
        """Loads a single dictionary object as a model into the database."""
        model = self._validate_and_load(item, table, validate)
        if model:
            self._database[table][model.slug] = model

    def reload(self, table: str, validate: bool = True) -> None:
        """Reloads the data for a specific table."""
        if table not in self._database:
            logger.error(f"Table '{table}' not initialized.")
            return

        logger.info(f"Clearing and resetting data for table '{table}'.")
        self._preloaded[table] = {}
        self._database[table] = {}

        try:
            # Preload from all mods associated with this table
            mods_associated = [
                mod
                for mod, tables in self._config.mod_tables.items()
                if table in tables and mod in self._config.active_mods
            ]

            # Note: Dependency order is technically lost here for a partial reload
            # unless a targeted dependency resolver is used. Assuming simple iteration
            # is acceptable.
            for mod in mods_associated:
                self._preload_table(table, mod)

            # Load into the database
            self._load_models_from_preloaded(table, validate)
        except Exception as e:
            logger.error(f"Error reloading table '{table}': {e}")

    def add_entry(
        self, table: str, data: dict[str, Any], validate: bool = True
    ) -> None:
        """Adds a new data entry to the specified table."""
        try:
            model = self._loader.load(data, table, validate)

            if table not in self._database:
                self._database[table] = {}

            if model.slug in self._database[table]:
                logger.error(
                    f"Entry with slug '{model.slug}' already exists in table '{table}'. Skipping addition."
                )
                return

            self._database[table][model.slug] = model
            logger.info(
                f"Entry '{model.slug}' added to table '{table}' successfully!"
            )

        except ValidationError as e:
            if validate:
                raise e
        except Exception as ex:
            logger.error(
                f"Unexpected error while adding entry to table '{table}': {ex}"
            )
