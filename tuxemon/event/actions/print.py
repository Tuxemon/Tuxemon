# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class PrintAction(EventAction):
    """
    Print the current value of one or more game variables to the console.

    If no variable is specified, print out values of all game variables.

    Script usage:
        .. code-block::

            print
            print <variables>

        Script parameters:
            variables: Optional, prints out the value of this/these variable/s,
                multiple variables separated by ':'.
    """

    name = "print"
    variables: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        if self.variables:
            variables = [var for var in self.variables.split(":") if var]
            for variable in variables:
                if player.game_variables and variable in player.game_variables:
                    print(f"{variable}: {player.game_variables[variable]}")
                else:
                    print(f"'{variable}' has not been set yet by map actions.")
        else:
            if player.game_variables:
                print(player.game_variables)
            else:
                print("No game variables have been set.")
