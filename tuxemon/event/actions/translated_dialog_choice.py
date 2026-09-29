# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.menu_options import MenuOptions, create_choice_options
from tuxemon.ui.text_formatter import TextFormatter

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

    def start(self, session: Session) -> None:
        def _set_variable(var_value: str, player: NPC) -> None:
            player.game_variables.set(self.variable, var_value)
            session.client.pop_state()

        # perform text substitutions
        choices = TextFormatter.replace_text(session, self.choices, T)
        player = session.client.get_npc("player")
        assert player

        # make menu options for each string between the colons
        var_list: list[str] = choices.split(":")

        actions = {
            val: partial(_set_variable, val, player) for val in var_list
        }
        options = create_choice_options(actions)

        open_choice_dialog(
            client=session.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
        )

    def update(self, session: Session, dt: float) -> None:
        if "ChoiceState" not in session.client.active_state_names:
            self.stop()
