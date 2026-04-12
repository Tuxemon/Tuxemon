# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import inspect
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, ClassVar

from tuxemon.cli.clicommand import CLICommand
from tuxemon.cli.context import InvokeContext
from tuxemon.cli.exceptions import CommandNotFoundError, ParseError
from tuxemon.cli.formatter import Formatter
from tuxemon.constants.paths import get_plugin_paths, mods_folder
from tuxemon.plugin import PluginManager

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class MetaCommand(CLICommand):
    """
    Command to use at the prompt. It is never invoked by name.

    Parameters:
        commands: Sequence of commands to make available at the prompt.
    """

    name: ClassVar[str] = "Meta Command"
    description: ClassVar[str] = "Root command container"

    def __init__(self, commands: Iterable[CLICommand]) -> None:
        self._commands: list[CLICommand] = list(commands)

    def invoke(self, ctx: InvokeContext, line: str) -> None:
        import sys

        print("No command provided. Available commands:", file=sys.stderr)
        for command in self._commands:
            print(f"- {command.name}: {command.description}", file=sys.stderr)

    def get_subcommands(self, ctx: InvokeContext) -> Iterable[CLICommand]:
        return self._commands


class CommandProcessor:
    """
    FastAPI-compatible command processor.
    No prompt_toolkit. No blocking input loop.
    """

    session: Session
    client: BaseClient
    formatter: Formatter
    root_command: MetaCommand
    commands: list[CLICommand]

    def __init__(self, session: Session) -> None:
        self.session = session
        self.client = session.client
        self.formatter = Formatter()

        commands = list(self.collect_commands())
        self.root_command = MetaCommand(commands)
        self.commands = commands

    def execute(self, line: str) -> dict[str, str]:
        """
        Parse a command string and queue it for execution
        on the main game thread.
        """

        ctx = InvokeContext(
            processor=self,
            session=self.session,
            root_command=self.root_command,
            current_command=self.root_command,
            formatter=self.formatter,
        )

        try:
            command, tail = self.root_command.resolve(ctx, line)

            # Thread‑safe: run inside the game loop
            self.client.queue_command(lambda: command.invoke(ctx, tail))

            return {
                "status": "queued",
                "command": command.name,
                "args": tail,
            }

        except ParseError as e:
            return {
                "status": "error",
                "type": "parse_error",
                "detail": str(e),
            }

        except CommandNotFoundError as e:
            return {
                "status": "error",
                "type": "not_found",
                "detail": str(e),
            }

        except Exception as e:
            logger.exception("Unhandled CLI error")
            return {
                "status": "error",
                "type": "internal",
                "detail": str(e),
            }

    def collect_commands(self) -> Iterable[CLICommand]:
        """
        Load CLICommand plugins from mods/*/commands/
        """

        existing_command_folders = get_plugin_paths(
            base_path=mods_folder,
            category="commands",
            subfolder=None,
        )

        if not existing_command_folders:
            logger.debug("No command folders found.")
            return []

        command_dict: dict[str, CLICommand] = {}

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
            logger.error("Error loading commands", exc_info=True)

        return command_dict.values()
