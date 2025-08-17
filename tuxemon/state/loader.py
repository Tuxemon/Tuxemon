# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import inspect
import logging
import sys
from collections.abc import Generator
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.state.repository import StateRepository
    from tuxemon.state.state import State

logger = logging.getLogger(__name__)


class StateLoader:
    """
    Handles the discovery, loading, and initial registration of game state
    classes.
    TODO: This discovery logic overlaps with the plugin system.
    For now, StateLoader handles static filesystem-based discovery.
    """

    def __init__(self, base_package: str, lib_dir: Path) -> None:
        """
        Initializes the StateLoader.

        Parameters:
            base_package: The base package name (e.g., "my_game.states") to
                scan for states.
            lib_dir: The base directory where game libraries are located
                (e.g., paths.LIBDIR).
        """
        self.base_package = base_package
        self.lib_dir = lib_dir

    @staticmethod
    def _collect_states_from_module(
        import_name: str,
    ) -> Generator[type[State], None, None]:
        """
        Given a module, return all classes in it that are a game state.
        """
        if import_name not in sys.modules:
            try:
                import_module(import_name)
            except ImportError as e:
                logger.error(
                    f"Failed to import module {import_name} during state collection: {e}"
                )
                return

        classes = inspect.getmembers(sys.modules[import_name], inspect.isclass)

        for c in (i[1] for i in classes):
            if issubclass(c, object) and c.__name__ != "State":
                try:
                    from .state import State as RealState

                    if issubclass(c, RealState) and not inspect.isabstract(c):
                        yield c
                except ImportError:
                    logger.warning(
                        "Could not import base 'State' class for type checking during discovery."
                    )

    def collect_states_from_path(
        self,
        folder: Path,
    ) -> Generator[type[State], None, None]:
        """
        Load states from disk, but do not register them.

        Parameters:
            folder: Folder to load from.

        Yields:
            Each game state class.
        """
        try:
            import_name = f"{self.base_package}.{folder.name}"
            import_module(import_name)
            yield from self._collect_states_from_module(import_name)
        except Exception as e:
            template = (
                "{} failed to load or is not a valid game state package: {}"
            )
            logger.error(template.format(folder.name, e))
            raise

    def auto_state_discovery(self, repository: StateRepository) -> None:
        """
        Scan a package's folder, load states found in it, and register them
        with the provided StateRepository.
        Supports both subfolders and flat .py files.
        """
        state_folder = self.lib_dir / Path(*self.base_package.split(".")[1:])
        logger.info(f"Initiating game state discovery from {state_folder}")

        if not state_folder.is_dir():
            logger.warning(
                f"State discovery path does not exist or is not a directory: {state_folder}"
            )
            return

        for entry in state_folder.iterdir():
            # Handle subfolders (legacy behavior)
            if entry.is_dir() and (entry / "__init__.py").exists():
                import_name = f"{self.base_package}.{entry.name}"
            # Handle flat .py files
            elif (
                entry.is_file()
                and entry.suffix == ".py"
                and entry.name != "__init__.py"
            ):
                import_name = f"{self.base_package}.{entry.stem}"
            else:
                continue

            logger.debug(f"Attempting to load states from: {import_name}")
            try:
                for state_cls in self._collect_states_from_module(import_name):
                    repository.add_state(state_cls)
                    state_name = getattr(state_cls, "name", state_cls.__name__)
                    logger.debug(f"Registered state: {state_name}")
            except Exception:
                logger.error(
                    f"Skipping '{entry.name}' due to errors during state collection.",
                    exc_info=True,
                )
