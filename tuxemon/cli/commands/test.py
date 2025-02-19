# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import sys
import traceback
from collections.abc import Iterable
from typing import TYPE_CHECKING

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.exceptions import ParseError
from tuxemon.event import MapCondition
from tuxemon.script.parser import parse_condition_string

if TYPE_CHECKING:
    from tuxemon.cli.context import InvokeContext


class TestConditionParentCommand(CLICommand):
    """
    Command that will test a condition.

    """

    name = "test"
    description = "Evaluate condition and print the result."
    example = "test player_facing up"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Default when no arguments are entered.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        print("need more arguments or syntax error", file=sys.stderr)

    def get_subcommands(self, ctx: InvokeContext) -> Iterable[CLICommand]:
        """
        Return subcommands that will evaluate an EventCondition.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.

        """
        conditions = ctx.session.client.event_engine.get_conditions()
        for condition in conditions:
            command = TestConditionCommand()
            command.name = condition.name
            command.description = getattr(condition, "__doc__")
            yield command


class TestConditionCommand(CLICommand):
    """
    Subcommand used by ``test`` to evaluate EventConditions.

    * "is" prefix is implied; do not include "is" or "not".

    """

    usable_from_root = False

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Test a condition.

        * do not use "is" or "not".

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        line = f"is {self.name} {line}"
        try:
            opr, typ, args = parse_condition_string(line)
            cond = MapCondition(typ, args, 0, 0, 0, 0, opr, "USERINPUT")
        except ValueError:
            raise ParseError
        try:
            result = ctx.session.client.event_engine.check_condition(cond)
            print(result)
        except Exception:
            traceback.print_exc()
            print(
                "Cannot test condition. Check the input and try again.",
                file=sys.stderr,
            )
