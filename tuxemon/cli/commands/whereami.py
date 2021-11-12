from __future__ import annotations

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext


class WhereAmICommand(CLICommand):
    """
    Display player map name

    """

    name = "whereami"
    description = "Print the filename of map where player is"
    example = "whereami"

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Display player map

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        try:
            filename = ctx.session.client.event_engine.current_map.data.filename
        except AttributeError:
            print("Cannot get filename from the game.")
        else:
            print(filename)
