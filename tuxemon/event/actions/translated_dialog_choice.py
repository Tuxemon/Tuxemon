# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T, replace_text
from tuxemon.states.choice import ChoiceState

logger = logging.getLogger(__name__)


@final
@dataclass
class TranslatedDialogChoiceAction(EventAction):
    """
    Ask the player to make a choice.

    Script usage:
        .. code-block::

            translated_dialog_choice <choices>,<variable>

    Script parameters:
        choices: List of possible choices, separated by a colon ":".
        variable: Variable to store the result of the choice.

    """

    name = "translated_dialog_choice"

    choices: str
    variable: str

    def start(self) -> None:
        def set_variable(var_value: str) -> None:
            player.game_variables[self.variable] = var_value
            self.session.client.pop_state()

        # perform text substitutions
        choices = replace_text(self.session, self.choices)
        maybe_player = get_npc(self.session, "player")
        assert maybe_player
        player = maybe_player

        # make menu options for each string between the colons
        var_list = choices.split(":")
        var_menu = list()

        for val in var_list:
            text = T.translate(val)
            var_menu.append((text, text, partial(set_variable, val)))

        self.session.client.push_state(
            ChoiceState(
                menu=var_menu,
            )
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(ChoiceState)
        except ValueError:
            self.stop()
