# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Union, final

from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar, string_to_colorlike
from tuxemon.locale import process_translate_text
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class TranslatedDialogAction(EventAction):
    """
    Open a dialog window with translated text according to the passed
    translation key. Parameters passed to the translation string will also
    be checked if a translation key exists.

    Script usage:
        .. code-block::

            translated_dialog <text>[,avatar][,style]

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.
        style: a predefined style in db/dialogue/dialogue.json

    """

    name = "translated_dialog"
    raw_parameters: str
    avatar: Union[int, str, None] = None
    style: Optional[str] = None

    def start(self) -> None:
        key = process_translate_text(self.session, self.raw_parameters, [])

        avatar_sprite = None
        if self.avatar:
            avatar_sprite = get_avatar(self.session, self.avatar)

        dialogue = self.style if self.style else "default"
        style = db.lookup(dialogue, table="dialogue")
        colors: dict[str, Any] = {
            "bg_color": string_to_colorlike(style.bg_color),
            "font_color": string_to_colorlike(style.font_color),
            "font_shadow": string_to_colorlike(style.font_shadow_color),
            "border": style.border_path,
        }

        open_dialog(
            session=self.session,
            text=key,
            avatar=avatar_sprite,
            colors=colors,
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()
