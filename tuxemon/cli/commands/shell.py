# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import code

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class ShellCommand(CLICommand):
    """
    Open python shell.

    """

    name = "shell"
    description = "Start interactive python shell."
    example = "shell"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Open a full python shell.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        print("Use the `ctx` object to interact with the game. CTRL-D exits.")
        code.interact(local=locals())
