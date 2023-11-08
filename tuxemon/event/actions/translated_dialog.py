# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, final

from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar, string_to_colorlike
from tuxemon.locale import process_translate_text
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)


@final
@dataclass
class TranslatedDialogAction(EventAction):
    """
    Open a dialog window with translated text according to the passed
    translation key. Parameters passed to the translation string will also
    be checked if a translation key exists.

    You may also use special variables in dialog events. Here is a list
    of available variables:

    * ${{name}} - The current player's name.

    Parameters following the translation name may represent one of two things:
    If a parameter is var1=value1, it represents a value replacement.
    If it's a single value (an integer or a string), it will be used as an
    avatar image.
    TODO: This is a hack and should be fixed later on, ideally without
    overloading the parameters.

    Script usage:
        .. code-block::

            translated_dialog <text>,<avatar>,<bg>,<font_color>,<font_shadow>,<border>
            translated_dialog <text>[,var1=value1]...

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.
        style: a predefined style in db/dialogue/dialogue.json

    """

    name = "translated_dialog"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args: Any) -> None:
        super().__init__()
        self.raw_parameters = args

    def start(self) -> None:
        key = self.raw_parameters[0]
        replace = []
        avatar = None
        if len(self.raw_parameters) >= 2:
            for param in self.raw_parameters[1]:
                if "=" in param:
                    replace.append(param)
                else:
                    avatar = get_avatar(self.session, param)

        dialogue = "default"

        if len(self.raw_parameters) >= 3:
            if len(self.raw_parameters[2]) > 0:
                dialogue = self.raw_parameters[2]

        style = db.lookup(dialogue, table="dialogue")

        colors: dict[str, Any] = {
            "bg_color": string_to_colorlike(style.bg_color),
            "font_color": string_to_colorlike(style.font_color),
            "font_shadow": string_to_colorlike(style.font_shadow_color),
            "border": style.border_path,
        }

        self.open_dialog(
            pages=process_translate_text(
                self.session,
                key,
                replace,
            ),
            avatar=avatar,
            colors=colors,
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def open_dialog(
        self,
        pages: Sequence[str],
        avatar: Optional[Sprite],
        colors: dict[str, str],
    ) -> None:
        logger.info("Opening dialog window")
        open_dialog(
            session=self.session, text=pages, avatar=avatar, colors=colors
        )
