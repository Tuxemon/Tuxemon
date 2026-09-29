# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar

from tuxemon.state.state import State

logger = logging.getLogger(__name__)

StateType = TypeVar("StateType", bound="State")


class StateBuilder(Generic[StateType]):
    def __init__(self, state_cls: type[StateType]) -> None:
        """
        Initializes the builder for a specific state class.

        Parameters:
            state_cls: The class of the state to be constructed.
        """
        self.state_cls = state_cls
        self.attributes: dict[str, Any] = {}

    def add_attribute(self, key: str, value: Any) -> StateBuilder[StateType]:
        """
        Add an attribute or parameter to the state.

        Parameters:
            key: The name of the attribute.
            value: The value of the attribute.

        Returns:
            The builder instance (for method chaining).
        """
        self.attributes[key] = value
        return self

    def load_attributes(
        self, attributes: dict[str, Any]
    ) -> StateBuilder[StateType]:
        """
        Loads multiple attributes into the builder at once.

        This method updates the internal attribute dictionary with the provided
        key-value pairs. It is useful for applying a predefined configuration or
        bulk initialization.

        Parameters:
            attributes: A dictionary where keys are attribute names and values are
                the corresponding values to be passed to the state's constructor.
        """
        self.attributes.update(attributes)
        return self

    def build(self) -> StateType:
        """
        Constructs the state instance with the specified attributes.

        Returns:
            An instance of the state class.
        """
        logger.debug(
            f"Building {self.state_cls.__name__} with attributes: {self.attributes}"
        )
        return self.state_cls(**self.attributes)
