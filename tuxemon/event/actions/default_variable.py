# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class DefaultVariableAction(EventAction):
    """
    Sets a default for a player game variable only when it is still unset.

    Script usage:
        .. code-block::

            default_variable <variable>:<value>

    Script parameters:
        variable: The name of the variable.
        value: The value to assign when the variable is still unset.

    Put this action right after a choice in a script. A choice that is
    closed with Back or Cancel leaves its variable unset, and this action
    then makes that count as <value> (for example the "Leave" option), so
    Back means "leave" instead of doing nothing. If the variable already
    holds any value, even the empty string, it is left alone.

    The pair is split at the first colon. If there is no colon or the
    variable name is empty, an error is logged and nothing happens.
    """

    name = "default_variable"

    pair: str

    def start(self, session: Session) -> None:
        var_key, sep, var_value = self.pair.partition(":")
        if not sep or not var_key:
            logger.error(
                "default_variable: malformed pair %r; expected <variable>:<value>",
                self.pair,
            )
            return

        player = session.player
        if player.game_variables.get(var_key) is None:
            player.game_variables.set(var_key, var_value)
