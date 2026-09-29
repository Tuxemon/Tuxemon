# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from tuxemon.database.config import DatabaseConfig
from tuxemon.database.yaml_utils import load_yaml

if TYPE_CHECKING:
    from tuxemon.db import DataModel

logger = logging.getLogger(__name__)


def load_dict(
    item: Mapping[str, Any],
    path: Path,
    preloaded_data: dict[str, Any],
) -> None:
    """Extracts slug and file path from a raw dict and adds it to preloaded data."""
    if not isinstance(item, dict):
        logger.error(f"Expected dict, got {type(item)} from {path}. Skipping.")
        return

    slug = item.get("slug")
    if slug is None:
        logger.error(
            f"Error: Item loaded from {path} is missing 'slug' key. Skipping."
        )
        return

    # Handle overwrites: Mod data loaded later overrides data loaded earlier
    # File path info is appended for tracking
    if slug not in preloaded_data:
        preloaded_data[slug] = dict(item)
        preloaded_data[slug]["paths"] = [path]
    elif path not in preloaded_data[slug].get("paths", []):
        # Update existing entry (later mod overrides earlier)
        preloaded_data[slug].update(item)
        preloaded_data[slug].setdefault("paths", []).append(path)
    else:
        logger.error(
            f"Error: Item with slug {slug} was already loaded from this path ({path})."
        )


def load_files(
    directory: str, path: Path, config: DatabaseConfig
) -> dict[str, Any]:
    """
    Loads all data files (JSON/YAML) from a directory path into a
    preloaded dictionary.
    """
    preloaded_data: dict[str, Any] = {}
    extensions = config.file_extensions
    directory_path = path / directory

    if not directory_path.exists():
        logger.debug(f"Directory not found: '{directory_path}'. Skipping.")
        return preloaded_data

    for entry in directory_path.iterdir():
        if entry.is_file() and entry.suffix in extensions:
            try:
                if entry.suffix == ".json":
                    with entry.open(encoding="utf-8") as fp:
                        item = json.load(fp)
                else:
                    item = load_yaml(entry)

                if isinstance(item, list):
                    for sub_item in item:
                        load_dict(sub_item, entry, preloaded_data)
                elif isinstance(item, dict):
                    load_dict(item, entry, preloaded_data)
                else:
                    logger.warning(
                        f"File '{entry}' did not contain a dict or list of dicts. Skipping."
                    )

            except (
                json.JSONDecodeError,
                FileNotFoundError,
            ) as e:
                logger.error(f"Error loading file '{entry}': {e}")

    return preloaded_data


class ModelLoader:
    """Responsible for validating and instantiating Pydantic DataModels."""

    def __init__(self, model_map: dict[str, type[DataModel]]):
        self.model_map = model_map

    def validate(self, item: Mapping[str, Any], table: str) -> DataModel:
        """Validates an item against its table's model class."""
        model_class = self.model_map.get(table)
        if not model_class:
            raise ValueError(f"Unexpected table: {table}")
        return model_class(**item)

    def load(
        self, item: Mapping[str, Any], table: str, validate: bool = False
    ) -> DataModel:
        """
        Loads an item, optionally validating it.
        Returns the instantiated DataModel or raises error if validation fails.
        """
        try:
            model_class = self.model_map.get(table)
            if not model_class:
                raise ValueError(f"Unexpected table: {table}")

            model = model_class(**item)
            if validate:
                # Re-validation is redundant if model was instantiated without error,
                # but kept here to reflect the original logic/intent.
                model_class(**item)
            return model

        except ValidationError as e:
            slug = item.get("slug", "unknown")
            logger.error(
                f"Validation failed for '{slug}' in table '{table}': {e}"
            )
            if validate:
                raise e
            # Re-raise runtime error if validation is false but loading failed unexpectedly
            raise RuntimeError(f"Failed to load item for table '{table}'.")
