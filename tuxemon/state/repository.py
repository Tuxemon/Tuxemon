# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.state.loader import StateLoader
    from tuxemon.state.state import State

logger = logging.getLogger(__name__)


class StateRepository:
    def __init__(self) -> None:
        self._state_dict: dict[str, type[State]] = {}

    @classmethod
    def from_loader(cls, loader: StateLoader) -> StateRepository:
        repo = cls()
        loader.auto_state_discovery(repo)
        return repo

    def add_state(self, state: type[State], strict: bool = False) -> None:
        """
        Adds a state to the repository.

        Parameters:
            state: The state class to register.
            strict: If True, raises an error if the state is already registered.
                Defaults to False.

        Raises:
            ValueError: If the state is already registered and strict is True.
        """
        name = state.__name__
        if name in self._state_dict:
            if strict:
                raise ValueError(f"State '{name}' is already registered.")
            else:
                logger.warning(
                    f"State '{name}' is already registered. Overwriting."
                )
        self._state_dict[name] = state

    def get_state(self, name: str) -> type[State]:
        """Retrieve a state by its name."""
        try:
            return self._state_dict[name]
        except KeyError:
            raise ValueError(f"State '{name}' is not registered.")

    def all_states(self) -> dict[str, type[State]]:
        """Retrieve all registered states."""
        return self._state_dict.copy()
