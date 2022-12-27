#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import Callable, Sequence, Tuple, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T, replace_text
from tuxemon.session import Session
from tuxemon.states.choice import ChoiceState
from tuxemon.tools import open_choice_dialog

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

        open_choice_dialog(
            self.session,
            menu=var_menu,
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(ChoiceState)
        except ValueError:
            self.stop()

    def open_choice_dialog(
        self,
        session: Session,
        menu: Sequence[Tuple[str, str, Callable[[], None]]],
    ) -> ChoiceState:
        logger.info("Opening choice window")
        return session.client.push_state(ChoiceState(menu=menu))
