# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import CommandNotFoundError, ParseError
from tuxemon.cli.formatter import Formatter
from tuxemon.plugin import (
    FileSystemPluginDiscovery,
    ImportLibPluginLoader,
    PluginFilter,
    PluginLoader,
    PluginManager,
    get_available_classes,
)

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient


class MetaCommand(CLICommand):
    """
    Command to use at the prompt.  It is never invoked by name.

    Parameters:
        commands: Sequence of commands to make available at the prompt.
    """

    name = "Meta Command"
    description = "Used as the primary command."

    def __init__(self, commands: Sequence[CLICommand]) -> None:
        self._commands = commands

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        """
        Default when no arguments are entered.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
            line: Input text after the command name.
        """
        print("No command provided. Available commands:", file=sys.stderr)
        for command in self._commands:
            print(f"- {command.name}: {command.description}", file=sys.stderr)

    def get_subcommands(self, ctx: InvokeContext) -> Iterable[CLICommand]:
        """
        Return commands that can be used at the prompt.

        Parameters:
            ctx: Contains references to parts of the game and CLI interface.
        """
        return self._commands


class CommandProcessor:
    """
    A class to enable an interactive debug command line.

    Parameters:
        client: LocalPygameClient which will be controlled by the debug prompt.
        prompt: Default text to display before the input area, ie "> ".
    """

    def __init__(self, client: LocalPygameClient, prompt: str = "> ") -> None:
        self.prompt = prompt
        self.client = client
        folder = Path(__file__).parent / "commands"
        # TODO: add folder(s) from mods
        commands = list(self.collect_commands(folder.as_posix()))
        self.root_command = MetaCommand(commands)

    def run(self) -> None:
        """
        Repeatedly get input from user, parse it, and run the commands.
        """
        ctx = InvokeContext(
            processor=self,
            client=self.client,
            root_command=self.root_command,
            current_command=self.root_command,
            formatter=Formatter(),
        )
        self.prompt_session: PromptSession[str] = PromptSession()

        while self.client.is_running:
            try:
                line = self.prompt_session.prompt(self.prompt)
                if line:
                    try:
                        command, tail = self.root_command.resolve(ctx, line)
                        ctx.current_command = command
                        command.invoke(ctx, tail)
                    except ParseError as e:
                        print(
                            f"Unknown syntax: {line} - {str(e)}",
                            file=sys.stderr,
                        )
                    except CommandNotFoundError as e:
                        print(
                            f"Cannot determine the command for: {line} - {str(e)}",
                            file=sys.stderr,
                        )
            except EOFError:
                break
            except KeyboardInterrupt:
                print("Got KeyboardInterrupt")
                print("Press CTRL-D to quit.")
                break

        self.quit()

    def quit(self) -> None:
        """
        Gracefully shuts down the command processor and exits the client.
        """
        self.client.quit()

    def collect_commands(self, folder: str) -> Iterable[CLICommand]:
        """
        Use plugins to load CLICommand classes for commands.

        Parameters:
            folder: Folder to search.
        """
        discovery = FileSystemPluginDiscovery([folder])
        loader = PluginLoader(ImportLibPluginLoader())
        filter = PluginFilter(
            include_patterns=["commands"], exclude_classes=["CLICommand"]
        )
        pm = PluginManager(discovery, loader, filter)
        pm.collect_plugins()
        for cmd_class in get_available_classes(pm, interface=CLICommand):
            if cmd_class.usable_from_root:
                yield cmd_class()
