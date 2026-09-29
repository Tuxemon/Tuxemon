# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from tuxemon.database.config import ModMetadata
from tuxemon.database.yaml_utils import load_yaml

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Manages mod load-order dependencies."""

    def __init__(self, mod_dependencies: dict[str, list[str]]) -> None:
        self.mod_dependencies = mod_dependencies

    def resolve(self, mod: str, visited: set[str] | None = None) -> list[str]:
        """Recursively resolves dependencies for a single mod."""
        if visited is None:
            visited = set()
        if mod in visited:
            return []

        visited.add(mod)
        dependencies = []
        if mod in self.mod_dependencies:
            for dep in self.mod_dependencies[mod]:
                dependencies.extend(self.resolve(dep, visited))
                dependencies.append(dep)

        # Return unique, ordered dependencies
        return list(dict.fromkeys(dependencies))


class ModMetadataLoader:
    """Loads and validates mod.yaml metadata files."""

    def __init__(
        self, active_mods: list[str], base_path: str = "mods"
    ) -> None:
        self.active_mods = active_mods
        self.base_path = Path(base_path)

    def load_metadata(self) -> dict[str, ModMetadata]:
        """Loads and returns metadata for all active mods."""
        metadata: dict[str, ModMetadata] = {}

        for mod_directory in self.active_mods:
            mod_path = self.base_path / mod_directory / "mod.yaml"

            if not mod_path.exists():
                logger.error(f"Metadata file missing: '{mod_path}'")
                continue

            try:
                raw_data = load_yaml(mod_path)
                validated_meta = ModMetadata(**raw_data)

                if validated_meta.slug != mod_directory:
                    logger.error(
                        f"Mod slug '{validated_meta.slug}' in '{mod_directory}/mod.yaml' "
                        f"does not match its directory name '{mod_directory}'. Skipping mod."
                    )
                    continue

                metadata[mod_directory] = validated_meta
                logger.info(
                    f"Loaded mod '{mod_directory}' version {validated_meta.version}"
                )

            except ValidationError as e:
                logger.error(
                    f"Metadata validation failed for '{mod_directory}' mod.yaml. {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error processing '{mod_directory}' metadata: {e}"
                )

        return metadata


class ModMetadataManager:
    """Provides access to loaded mod metadata."""

    def __init__(self, mod_metadata: dict[str, ModMetadata]) -> None:
        self._mod_metadata = mod_metadata

    def get_mod_attribute(
        self, mod_name: str, attribute_name: str
    ) -> Any | None:
        """Retrieves a specific attribute (field) from a mod's metadata."""
        mod_meta = self._mod_metadata.get(mod_name)
        if mod_meta:
            return getattr(mod_meta, attribute_name, None)
        return None

    def require_mod_attribute(self, mod_name: str, attribute_name: str) -> Any:
        """Retrieves an attribute or raises ValueError if missing."""
        value = self.get_mod_attribute(mod_name, attribute_name)
        if value is None:
            raise ValueError(
                f"mod.yaml in '{mod_name}' lacks required attribute '{attribute_name}'"
            )
        return value

    def get_mod_metadata(self, mod_name: str) -> ModMetadata:
        """Returns the full ModMetadata instance."""
        mod_meta = self._mod_metadata.get(mod_name)
        if not mod_meta:
            raise ValueError(f"Metadata for mod '{mod_name}' not found.")
        return mod_meta
