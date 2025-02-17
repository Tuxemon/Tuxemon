# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class RandomEncounterCommand(CLICommand):
    """
    Start random encounter using "default_encounter".

    """

    name = "random_encounter"
    description = "Start random encounter using 'default_encounter'."
    example = "random_encounter"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Start random encounter using "default_encounter".

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Complete text as entered into the prompt.

        """
        ctx.session.client.event_engine.execute_action(
            "random_encounter", ["default_encounter", 100]
        )
