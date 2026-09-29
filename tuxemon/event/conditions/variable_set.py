# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class VariableSetCondition(EventCondition):
    """
    Checks whether one or more player game variables exist and optionally
    match specific values.

    Script usage:
        .. code-block::

            is variable_set <variable>[:value],[<variable>[:value] ...]

    Script parameters:
        variable: The first variable to check.
        value: Optional value for the first variable.
    """

    name: ClassVar[str] = "variable_set"
    required_vars: list[tuple[str, str | None]] = field(
        default_factory=list, init=False
    )

    def __init__(self, *args: str):
        self.required_vars = []

        for arg in args:
            if ":" in arg:
                key, _, val = arg.partition(":")
                self.required_vars.append((key, val if val != "" else None))
            else:
                self.required_vars.append((arg, None))

        self.__post_init__()

    def test(self, session: Session) -> bool:
        player = session.player

        for key, expected in self.required_vars:
            if not player.game_variables.has(key):
                return False
            if (
                expected is not None
                and player.game_variables.get(key) != expected
            ):
                return False

        return True
