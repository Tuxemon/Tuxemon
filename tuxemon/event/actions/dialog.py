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
import warnings
from typing import NamedTuple, Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar
from tuxemon.locale import replace_text
from tuxemon.sprite import Sprite
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


class DialogActionParameters(NamedTuple):
    text: str
    avatar: str


@final
class DialogAction(EventAction[DialogActionParameters]):
    """
    Open a single dialog and waits until it is closed.

    You may also use special variables in dialog events.
    Here is a list of available variables:

    * ${{name}} - The current player's name.

    Script usage:
        .. code-block::

            dialog <text>,<avatar>

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.

    """

    name = "dialog"
    param_class = DialogActionParameters

    def start(self) -> None:
        warnings.warn(
            f"Found deprecated dialog action, please use "
            f"translated_dialog instead. "
            f"Action: {self.name}. "
            f"Parameters: {self.raw_parameters}.",
            DeprecationWarning,
        )
        text = replace_text(self.session, self.parameters.text)
        avatar = get_avatar(self.session, self.parameters.avatar)
        self.open_dialog(text, avatar)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def open_dialog(self, initial_text: str, avatar: Optional[Sprite]) -> None:
        logger.info("Opening dialog window")
        open_dialog(self.session, [initial_text], avatar)
