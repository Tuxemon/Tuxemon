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
class VariableLowestCondition(EventCondition):
    """
    Check if a specific variable is the lowest among the others.

    Script usage:
        .. code-block::

            is variable_lowest <key_to_check>,<keys_to_check>

    Script parameters:
        key_to_check: Key to check.
        keys_to_check: List of the keys among to check separated by ':'

    Example:
        is variable_lowest jimmy,arthur:jimmy:clara
    """

    name = "variable_lowest"

    def test(self, session: Session, condition: MapCondition) -> bool:
        game_variables = session.player.game_variables
        key_to_check, _keys_to_check = condition.parameters
        keys_to_check = _keys_to_check.split(":")

        if key_to_check not in game_variables:
            logger.error(f"{key_to_check} is not in the game variables.")
            return False

        lowest_value, lowest_keys = find_lowest_value_and_keys(
            game_variables, keys_to_check
        )

        if len(lowest_keys) > 1:
            logger.error(
                f"Multiple lowest keys found: {lowest_keys} with value {lowest_value}"
            )

        return key_to_check == lowest_keys[0] if lowest_keys else False


def find_lowest_value_and_keys(
    game_variables: dict[str, Any], keys_to_check: list[str]
) -> tuple[float, list[str]]:
    lowest_value = float("inf")
    lowest_keys = []

    for key in keys_to_check:
        if key in game_variables:
            value = game_variables[key]
            try:
                value = float(value)
            except ValueError:
                raise ValueError(f"The value of '{key}' is not a number")
            if value < lowest_value:
                lowest_value = value
                lowest_keys = [key]
            elif value == lowest_value:
                lowest_keys.append(key)

    return lowest_value, lowest_keys
