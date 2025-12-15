# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.npc import NPC
from tuxemon.session import Session
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions
from tuxemon.ui.text_formatter import TextFormatter

logger = logging.getLogger(__name__)


@final
@dataclass
class ChoiceItemAction(EventAction):
    """
    Ask the player to make a choice among items.

    Script usage:
        .. code-block::

            choice_item <choices>,<variable>

    Script parameters:
        choices: List of possible choices
            (item slugs eg: potion:tea),
            separated by a colon ":".
        variable: Variable to store the result of the choice.
    """

    name = "choice_item"

    choices: str
    variable: str

    def start(self, session: Session) -> None:
        def _set_variable(var_value: str, player: NPC) -> None:
            player.game_variables.set(self.variable, var_value)
            session.client.pop_state()

        # perform text substitutions
        choices = TextFormatter.replace_text(session, self.choices, T)
        player = session.player

        # make menu options for each string between the colons
        var_list: list[str] = choices.split(":")
        options: list[ChoiceOption] = []

        for val in var_list:
            text = T.translate(val)
            action = partial(_set_variable, val, player)
            options.append(
                ChoiceOption(key=val, display_text=text, action=action)
            )

        session.client.push_state("ChoiceItem", menu=MenuOptions(options))

    def update(self, session: Session, dt: float) -> None:
        try:
            session.client.get_state_by_name("ChoiceItem")
        except ValueError:
            self.stop()
