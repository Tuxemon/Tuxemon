# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import sys

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class WhereAmICommand(CLICommand):
    """
    Display player map name.

    """

    name = "whereami"
    description = "Print the filename of map where player is."
    example = "whereami"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Display player map

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        current_map = ctx.session.client.event_engine.current_map
        if current_map:
            name = current_map.data.filename
            print(name)
        else:
            print("Cannot get filename from the game.", file=sys.stderr)
