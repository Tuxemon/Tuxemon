from __future__ import annotations

import traceback

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import ParseError
from tuxemon.cli.parser import parse
from tuxemon.event.actions.start_battle import StartBattleActionParameters


class TrainerBattleCommand(CLICommand):
    """
    Command to start a trainer battle

    """

    name = "trainer_battle"
    description = "Start a trainer battle"
    example = "trainer_battle maple_girl"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Start a trainer battle

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Complete text as entered into the prompt.

        """
        args = parse(line)
        if not args:
            print("Missing arguments: <npc_slug>")
            raise ParseError
        elif len(args) == 1:
            trainer = args[0]
            try:
                action = ctx.session.client.event_engine.execute_action
                action("create_npc", (trainer, 7, 6))
                action("start_battle", (StartBattleActionParameters(npc_slug=trainer)))
                action("remove_npc", (trainer,))
            except:
                traceback.print_exc()
