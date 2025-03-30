# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.processor import MetaCommand


class HelpCommand(CLICommand):
    """
    Command to get list available commands and display help for them.

    """

    name = "help"
    description = "Get help"
    example = "help"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        List available commands and display help for them.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        command, tail = ctx.root_command.resolve(ctx, line)
        if command is not ctx.root_command:
            print(command.description)
            print()
        if command.example:
            print("Example:")
            print(f"  > {command.example}")
            print()
        parameters = command.get_parameters(ctx)
        if parameters:
            names = sorted([p.name for p in parameters])
            if isinstance(command, MetaCommand):
                footer = "Enter 'help [command]' for more info."
            else:
                footer = f"Enter 'help {command.name} [option]' for more info."
            ctx.formatter.print_table("Available Options", names, footer)
