# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import string_to_colorlike
from tuxemon.locale.locale import T
from tuxemon.monster.avatar import get_avatar
from tuxemon.session import Session
from tuxemon.tools import open_dialog, safe_enum_value
from tuxemon.ui.dialogue import DialogueStyleCache
from tuxemon.ui.text_alignment import (
    DialogPosition,
    HorizontalAlignment,
    VerticalAlignment,
)
from tuxemon.ui.text_formatter import TextFormatter

logger = logging.getLogger(__name__)

style_cache = DialogueStyleCache()


@final
@dataclass
class CipherDialogAction(EventAction):
    """
    Displays a dialog window with text that may be ciphered based on the character's
    unlocked letters and the active CipherProcessor.

    The dialog text is optionally translated, styled, and formatted based on script
    parameters. Any unlocked letters will remain visible, while the remaining content
    may be obfuscated depending on the cipher configuration.

    Script usage:
        .. code-block::

            cipher_dialog <text>[,avatar][,position][,style]

    Script parameters:
        text: Text of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright', 'right', 'left'.
            Default 'bottom'.
        h_alignment: Alignment of text in the dialog box, it can be 'left', 'center'
            or 'right'. Default 'left'.
        v_alignment: Alignment of text in the dialog box, it can be 'bottom',
            'center' or 'top'. Default 'top'.
        style: a predefined style in db/dialogue/dialogue.json
    """

    name = "cipher_dialog"
    raw_parameters: str
    avatar: str | None = None
    position: str | None = None
    h_alignment: str | None = None
    v_alignment: str | None = None
    style: str | None = None

    def start(self, session: Session) -> None:
        cipher_processor = session.client.cipher_processor
        key = TextFormatter(
            session=session,
            translator=T,
            cipher_processor=cipher_processor,
        ).paginate_translation(self.raw_parameters)

        if key == self.raw_parameters:
            logger.warning(
                f"No translation found for key: {self.raw_parameters}"
            )

        avatar_sprite = (
            get_avatar(session, self.avatar) if self.avatar else None
        )

        dialogue = self.style or session.client.config.dialog_box_style
        style = style_cache.get(dialogue)
        h_alignment = safe_enum_value(
            HorizontalAlignment, self.h_alignment, HorizontalAlignment.LEFT
        )
        v_alignment = safe_enum_value(
            VerticalAlignment, self.v_alignment, VerticalAlignment.TOP
        )
        box_style: dict[str, Any] = {
            "bg_color": string_to_colorlike(style.bg_color),
            "font_color": string_to_colorlike(style.font_color),
            "font_shadow": string_to_colorlike(style.font_shadow_color),
            "border": style.border_path,
            "line_spacing": style.line_spacing,
            "h_alignment": h_alignment,
            "v_alignment": v_alignment,
        }

        position = safe_enum_value(
            DialogPosition, self.position, DialogPosition.BOTTOM
        )
        open_dialog(
            client=session.client,
            text=key,
            avatar=avatar_sprite,
            box_style=box_style,
            position=position,
            target_coords=None,
            custom_rect=None,
        )

    def update(self, session: Session, dt: float) -> None:
        if "DialogState" not in session.client.active_state_names:
            self.stop()
