# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING, Iterable

from tuxemon.cli.clicommand import CLICommand
from tuxemon.script.parser import parse_action_string

if TYPE_CHECKING:
    from tuxemon.cli.context import InvokeContext


class ActionParentCommand(CLICommand):
    """
    Command allows actions to be executed directly.

    Actions are listed as options, but when invoked, return
    subcommands that will execute the action.

    """

    name = "action"
    description = "Execute action in the game."
    example = "action add_item potion,10"

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
        Return subcommands that will execute an EventAction.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.

        """
        actions = ctx.session.client.event_engine.get_actions()
        for action in actions:
            command = ActionCommand()
            command.name = action.name
            command.description = getattr(action, "__doc__")
            yield command


class ActionCommand(CLICommand):
    """
    Subcommand used by ``action`` to invoke EventActions.

    """

    usable_from_root = False

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Execute action directly.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        line = f"{self.name} {line}"
        name, args = parse_action_string(line)
        try:
            ctx.session.client.event_engine.execute_action(name, args)
        except Exception as exc:
            traceback.print_exc()
            print(
                "Cannot execute action. Check the input and try again.",
                file=sys.stderr,
            )
