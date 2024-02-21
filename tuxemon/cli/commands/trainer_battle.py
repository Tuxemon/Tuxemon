# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import traceback

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import ParseError
from tuxemon.cli.parser import parse

# from tuxemon.event.actions.start_battle import StartBattleActionParameters


class TrainerBattleCommand(CLICommand):
    """
    Command to start a trainer battle.

    """

    name = "trainer_battle"
    description = "Start a trainer battle."
    example = "trainer_battle npc_test"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Start a trainer battle

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Complete text as entered into the prompt.

        """
        args = parse(line)
        if not args:
            print("Missing arguments: <character>")
            raise ParseError
        elif len(args) == 1:
            trainer = args[0]
            try:
                action = ctx.session.client.event_engine.execute_action
                action("create_npc", (trainer, 7, 6))
                action("start_battle", (trainer,))
                action("remove_npc", (trainer,))
            except Exception:
                traceback.print_exc()
