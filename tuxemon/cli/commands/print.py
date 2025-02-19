# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class PrintCommand(CLICommand):
    """
    Print variables set by map event actions.

    """

    name = "print"
    description = "Print values of variables set using map actions and events."
    example = "print name_variable"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Print values of variables set using map actions and events.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Complete text as entered into the prompt.

        """
        variable = line.strip()
        if variable:
            if variable in ctx.session.player.game_variables:
                print(
                    f"{variable}: {ctx.session.player.game_variables[variable]}"
                )
            else:
                print(f"'{variable}' has not been set yet by map actions.")
        else:
            print(ctx.session.player.game_variables)
