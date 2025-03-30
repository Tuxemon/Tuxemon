# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import ABC
from collections.abc import Iterable
from typing import TYPE_CHECKING, ClassVar

from tuxemon.cli.exceptions import CommandNotFoundError
from tuxemon.cli.parameter import Parameter
from tuxemon.cli.parser import split

if TYPE_CHECKING:
    from tuxemon.cli.context import InvokeContext


class CLICommand(ABC):
    """
    Base class for CLIOptions.

    """

    name: ClassVar[str] = "command name"
    description: ClassVar[str] = "command description"
    usable_from_root: ClassVar[bool] = True
    example: ClassVar[str] = ""

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Called when command input contains this command name as first term.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """

    def get_parameters(self, ctx: InvokeContext) -> Iterable[Parameter]:
        """
        Return parameters for use by help or autocomplete.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.

        """
        for cmd in self.get_subcommands(ctx):
            yield Parameter(cmd.name)

    def get_subcommands(self, ctx: InvokeContext) -> Iterable[CLICommand]:
        """
        Return all subcommands of this command.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.

        """
        return ()

    def get_subcommand(self, ctx: InvokeContext, name: str) -> CLICommand:
        """
        Return a single subcommand by name.

        If not implemented by subclass, then this will do a simple search
        by name of all subcommands as returned by ``self.get_subcommands``.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            name: Name of the action, in the form that it would be typed.

        Raises:
            CommandNotFoundError: If command by name is not found.

        """
        for command in self.get_subcommands(ctx):
            if command.name == name:
                return command
        raise CommandNotFoundError(f"Command '{name}' not found")

    def resolve(self, ctx: InvokeContext, path: str) -> tuple[CLICommand, str]:
        """
        Resolve a path into command and remaining text.

        * Split the command into tokens.
        * Starting from the first token, search it for the next token.
        * If the next token is a subcommand, repeat.
        * If the next token is not a subcommand, return command and the rest
          of the input.

        For example:
            The string "action char_face player up" will be parsed by
            checking each CLICommand for sub commands in a graph search.
            Starting at the root, which is unnamed, it will have an "action"
            command.  Then searching "action", it will have "char_face".
            `char_face` is a command, but doesn't have "player" as a subcommand,
            so the remaining portion of the string will be treated as an
            argument to "char_face".

        """
        head, tail = split(path)
        try:
            command = self.get_subcommand(ctx, head)
        except CommandNotFoundError:
            return self, path
        else:
            return command.resolve(ctx, tail)
