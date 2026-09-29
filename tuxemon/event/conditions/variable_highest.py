# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

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

    name: ClassVar[str] = "variable_highest"
    key_to_check: str
    keys_to_check: str

    def test(self, session: Session) -> bool:
        game_variables = session.player.game_variables
        keys_to_check = self.keys_to_check.split(":")

        if not game_variables.has(self.key_to_check):
            logger.error(f"{self.key_to_check} is not in the game variables.")
            return False

        highest_value, highest_keys = game_variables.find_highest(
            keys_to_check
        )

        if len(highest_keys) > 1:
            logger.error(
                f"Multiple highest keys found: {highest_keys} with value {highest_value}"
            )

        return self.key_to_check == highest_keys[0] if highest_keys else False
