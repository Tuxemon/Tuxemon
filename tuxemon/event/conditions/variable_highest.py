# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
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

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        game_variables = session.player.game_variables
        key_to_check, _keys_to_check = condition.parameters
        keys_to_check = _keys_to_check.split(":")

        if not game_variables.has(key_to_check):
            logger.error(f"{key_to_check} is not in the game variables.")
            return False

        highest_value, highest_keys = game_variables.find_highest(
            keys_to_check
        )

        if len(highest_keys) > 1:
            logger.error(
                f"Multiple highest keys found: {highest_keys} with value {highest_value}"
            )

        return key_to_check == highest_keys[0] if highest_keys else False
