# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Sequence, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar
from tuxemon.locale import process_translate_text
from tuxemon.sprite import Sprite
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class TranslatedDialogChainAction(
    EventAction,
):
    """
    Open a chain of dialogs in order.

    Dialog chain must be ended with the ${{end}} keyword. You may also use
    special variables in dialog events. Here is a list of available variables:

    * ${{name}} - The current player's name.
    * ${{end}} - Ends the dialog chain.

    If a parameter is var1=value1, it represents a value replacement.
    If it's a single value (an integer or a string), it will be used as an
    avatar image.
    TODO: This is a hack and should be fixed later on, ideally without
    overloading the parameters.

    Script usage:
        .. code-block::

            translated_dialog_chain <text>,<avatar>

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.

    """

    name = "translated_dialog_chain"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args):
        super().__init__()
        self.raw_parameters = args

    def start(self) -> None:
        key = self.raw_parameters[0]
        replace = []
        avatar = None
        for param in self.raw_parameters[1:]:
            if "=" in param:
                replace.append(param)
            else:
                avatar = get_avatar(self.session, param)

        # If text is "${{end}}, then close the current dialog
        if key == "${{end}}":
            return

        self.stop()

        pages = process_translate_text(
            self.session,
            key,
            replace,
        )

        try:
            dialog = self.session.client.get_state_by_name(DialogState)
            dialog.text_queue += pages
        except ValueError:
            self.open_dialog(pages, avatar)

    def update(self) -> None:
        key = self.raw_parameters[0]
        if key == "${{end}}":
            try:
                self.session.client.get_state_by_name(DialogState)
            except ValueError:
                self.stop()

    def open_dialog(
        self,
        pages: Sequence[str],
        avatar: Optional[Sprite],
    ) -> None:
        logger.info("Opening chain dialog window")
        open_dialog(self.session, pages, avatar)
