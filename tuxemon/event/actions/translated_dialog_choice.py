# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T, replace_text
from tuxemon.npc import NPC
from tuxemon.states.choice.choice_state import ChoiceState

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
        def _set_variable(var_value: str, player: NPC) -> None:
            player.game_variables[self.variable] = var_value
            self.session.client.pop_state()

        # perform text substitutions
        choices = replace_text(self.session, self.choices)
        player = get_npc(self.session, "player")
        assert player

        # make menu options for each string between the colons
        var_list: list[str] = choices.split(":")
        var_menu: list[tuple[str, str, Callable[[], None]]] = []

        for val in var_list:
            text = T.translate(val)
            var_menu.append((text, text, partial(_set_variable, val, player)))

        self.session.client.push_state(ChoiceState(menu=var_menu))

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(ChoiceState)
        except ValueError:
            self.stop()
