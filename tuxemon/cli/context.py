# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.cli.clicommand import CLICommand
    from tuxemon.cli.formatter import Formatter
    from tuxemon.cli.processor import CommandProcessor
    from tuxemon.session import Session


@dataclasses.dataclass
class InvokeContext:
    """
    Context object for use by CLICommands.

    """

    processor: CommandProcessor
    session: Session
    root_command: CLICommand
    current_command: CLICommand
    formatter: Formatter
