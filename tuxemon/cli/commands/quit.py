# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class QuitCommand(CLICommand):
    """
    Quit the game.

    """

    name = "quit"
    description = "Quit the game."
    example = "quit"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Quit the game.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Complete text as entered into the prompt.

        """
        ctx.session.client.event_engine.execute_action("quit")
