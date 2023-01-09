# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import os
import sys
from typing import Iterable

from prompt_toolkit import PromptSession

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import CommandNotFoundError, ParseError
from tuxemon.cli.formatter import Formatter
from tuxemon.plugin import PluginManager, get_available_classes
from tuxemon.session import Session


class MetaCommand(CLICommand):
    """
    Command to use at the prompt.  It is never invoked by name.

    Parameters:
        commands: Sequence of commands to make available at the prompt.

    """

    name = "Meta Command"
    description = "Used as the primary command."

    def __init__(self, commands):
        self._commands = commands

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Default when no arguments are entered.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.

        """
        print("???", file=sys.stderr)

    def get_subcommands(self, ctx: InvokeContext) -> Iterable[CLICommand]:
        """
        Return commands that can be used at the prompt.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.

        """
        return list(self._commands)


class CommandProcessor:
    """
    A class to enable an interactive debug command line.

    Parameters:
        session: Session which will be controlled by the debug prompt.
        prompt: Default text to display before the input area, ie "> ".

    """

    def __init__(self, session: Session, prompt: str = "> ") -> None:
        self.prompt = prompt
        self.session = session
        folder = os.path.join(os.path.dirname(__file__), "commands")
        # TODO: add folder(s) from mods
        commands = list(self.collect_commands(folder))
        self.root_command = MetaCommand(commands)

    def run(self) -> None:
        """
        Repeatedly get input from user, parse it, and run the commands.

        """
        ctx = InvokeContext(
            processor=self,
            session=self.session,
            root_command=self.root_command,
            current_command=self.root_command,
            formatter=Formatter(),
        )
        session = PromptSession()

        while True:
            try:
                try:
                    ctx.current_command = self.root_command
                    line = session.prompt(self.prompt)
                except EOFError:
                    break

                if line:
                    try:
                        command, tail = self.root_command.resolve(ctx, line)
                        ctx.current_command = command
                        command.invoke(ctx, tail)
                    except ParseError:
                        print(f"Unknown syntax: {line}", file=sys.stderr)
                    except CommandNotFoundError:
                        print(
                            f"Cannot determine the command for: {line}",
                            file=sys.stderr,
                        )

            except KeyboardInterrupt:
                print(f"Got KeyboardInterrupt")
                print(f"Press CTRL-D to quit.")

        event_engine = self.session.client.event_engine
        event_engine.execute_action("quit")

    def collect_commands(self, folder: str) -> Iterable[CLICommand]:
        """
        Use plugins to load CLICommand classes for commands.

        Parameters:
            folder: Folder to search.

        """
        pm = PluginManager()
        pm.setPluginPlaces([folder])
        pm.include_patterns = ["commands"]
        pm.exclude_classes = ["CLICommand"]
        pm.collectPlugins()
        for cmd_class in get_available_classes(pm, interface=CLICommand):
            if cmd_class.usable_from_root:
                yield cmd_class()
