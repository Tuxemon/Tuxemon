from __future__ import annotations

import code

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class ShellCommand(CLICommand):
    """
    Open python shell

    """

    name = "shell"
    description = "Start interactive python shell"
    example = "shell"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Open a full python shell

        Parameters:
            ctx:
            line: Input text after the command name.

        """
        print("Use the `ctx` object to interact with the game. CTRL-D exits.")
        code.interact(local=locals())
