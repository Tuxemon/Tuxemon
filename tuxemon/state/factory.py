# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from tuxemon.state.builder import StateBuilder

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.state.repository import StateRepository
    from tuxemon.state.state import State

logger = logging.getLogger(__name__)


class StateFactory:
    """
    Responsible for creating and configuring new State instances,
    using StateBuilder for construction.
    """

    def __init__(
        self, client: BaseClient, state_repository: StateRepository
    ) -> None:
        """
        Initializes the factory with a StateRepository to look up state classes.
        """
        self._client = client
        self._state_repository = state_repository

    def create_state(self, state_name: str, **kwargs: Any) -> State:
        """
        Creates a new instance of a State based on its name and provided arguments.
        Delegates construction to StateBuilder.

        Parameters:
            state_name: The string name of the state class to instantiate.
            kwargs: Keyword arguments to pass to the state's constructor.

        Returns:
            A new instance of the specified State.

        Raises:
            RuntimeError: If the state with the given name cannot be found.
        """
        logger.debug(
            f"Attempting to create state: '{state_name}' with attributes: {kwargs}"
        )
        try:
            state_cls = self._state_repository.get_state(state_name)
            logger.debug(f"Found state class: {state_cls.__name__}")
        except KeyError:
            logger.error(f"State '{state_name}' not found in repository")
            raise RuntimeError(f"Cannot find state: {state_name}")

        builder = StateBuilder(state_cls)
        builder.add_attribute("client", self._client)
        for key, value in kwargs.items():
            builder.add_attribute(key, value)

        instance = builder.build()
        logger.debug(f"Successfully built state instance: {instance}")
        return instance
