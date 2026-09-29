# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import inspect
import logging
import sys
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import CommandNotFoundError, ParseError
from tuxemon.cli.formatter import Formatter
from tuxemon.constants.paths import get_plugin_paths, mods_folder
from tuxemon.plugin import PluginManager

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


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
        session: Session which will be controlled by the debug prompt.
        prompt: Default text to display before the input area, ie "> ".
    """

    def __init__(self, session: Session, prompt: str = "> ") -> None:
        self.prompt = prompt
        self.session = session
        self.client = session.client
        commands = list(self.collect_commands())
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

    def collect_commands(self) -> Iterable[CLICommand]:
        """
        Use plugins to load CLICommand classes from all mod folders.
        """
        existing_command_folders = get_plugin_paths(
            base_path=mods_folder,
            category="commands",
            subfolder=None,
        )

        if not existing_command_folders:
            logger.debug("No existing command folders to search.")
            return []

        command_dict = {}

        try:
            pm = PluginManager.from_directory(
                plugin_folders=existing_command_folders,
                root_path=mods_folder.parent,
                include=["commands"],
                exclude=["CLICommand"],
            )

            logger.info(f"Discovered plugin modules: {pm.modules}")

            for plugin in pm.get_all_plugins(interface=CLICommand):
                cmd_class = plugin.plugin_object

                if (
                    not inspect.isabstract(cmd_class)
                    and cmd_class.usable_from_root
                ):
                    if cmd_class.name in command_dict:
                        logger.warning(
                            f"Overwriting command '{cmd_class.name}' "
                            f"from {cmd_class.__module__}"
                        )

                    command_dict[cmd_class.name] = cmd_class()
                    logger.info(f"Registered command: {cmd_class.name}")

        except Exception:
            logger.error(
                "Error loading commands from mod folders", exc_info=True
            )

        return command_dict.values()
