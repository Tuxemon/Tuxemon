# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class VariableHighestCondition(EventCondition):
    """
    Check if a specific variable is the highest among the others.

    Script usage:
        .. code-block::

            is variable_highest <key_to_check>,<keys_to_check>

    Script parameters:
        key_to_check: Key to check.
        keys_to_check: List of the keys among to check separated by ':'

    Example:
        is variable_highest jimmy,arthur:jimmy:clara
    """

    name = "variable_highest"

    def test(self, session: Session, condition: MapCondition) -> bool:
        game_variables = session.player.game_variables
        key_to_check, _keys_to_check = condition.parameters
        keys_to_check = _keys_to_check.split(":")

        if key_to_check not in game_variables:
            logger.error(f"{key_to_check} is not in the game variables.")
            return False

        highest_value, highest_keys = find_highest_value_and_keys(
            game_variables, keys_to_check
        )

        if len(highest_keys) > 1:
            logger.error(
                f"Multiple highest keys found: {highest_keys} with value {highest_value}"
            )

        return key_to_check == highest_keys[0] if highest_keys else False


def find_highest_value_and_keys(
    game_variables: dict[str, Any], keys_to_check: list[str]
) -> tuple[float, list[str]]:
    highest_value = float("-inf")
    highest_keys = []

    for key in keys_to_check:
        if key in game_variables:
            value = game_variables[key]
            try:
                value = float(value)
            except ValueError:
                raise ValueError(f"The value of '{key}' is not a number")
            if value > highest_value:
                highest_value = value
                highest_keys = [key]
            elif value == highest_value:
                highest_keys.append(key)

    return highest_value, highest_keys
