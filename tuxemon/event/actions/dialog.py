# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Optional, Sequence, final

from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar
from tuxemon.locale import replace_text
from tuxemon.sprite import Sprite
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class DialogAction(EventAction):
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
    text: str = field(init=False)
    avatar: Optional[str] = field(init=False)
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args):
        super().__init__()
        self.raw_parameters = args

        self.avatar = None
        if len(self.raw_parameters) > 1:
            avatar_str = self.raw_parameters[-1]
            if avatar_str.isdigit() or db.has_entry(avatar_str, "monster"):
                self.avatar = avatar_str

        if self.avatar:
            # hack to allow unescaped commas in the dialog string
            self.text = ", ".join(self.raw_parameters[:-1])
        else:
            # If we were unable to load an avatar then this was
            # probably normal text
            self.text = ", ".join(self.raw_parameters)

    def start(self) -> None:
        warnings.warn(
            f"Found deprecated dialog action, please use "
            f"translated_dialog instead. "
            f"Action: {self.name}. "
            f"Parameters: {self.raw_parameters}.",
            DeprecationWarning,
        )
        text = replace_text(self.session, self.text)
        self.open_dialog(text, get_avatar(self.session, self.avatar))

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def open_dialog(self, initial_text: str, avatar: Optional[Sprite]) -> None:
        logger.info("Opening dialog window")
        open_dialog(self.session, [initial_text], avatar)
