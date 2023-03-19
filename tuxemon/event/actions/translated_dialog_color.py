# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Sequence, final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import process_translate_text
from tuxemon.menu.menu import BACKGROUND_COLOR, FONT_COLOR
from tuxemon.menu.theme import get_theme
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class TranslatedDialogColorAction(EventAction):
    """
    It allows to change font color, shadow color (font) and
    background color.

    Script usage:
        .. code-block::

            translated_dialog_color <text>,<font_color>,<bg_color>,[shadow_color]

    Script parameters:
        text: msgid PO file.

    """

    name = "translated_dialog_color"
    raw_parameters: str

    def start(self) -> None:
        theme = get_theme()
        theme.background_color = (0, 0, 0)
        theme.widget_font_color = (0, 0, 0)
        theme.widget_font_shadow_color = (0, 0, 0)
        key = self.raw_parameters
        replace: Iterable[str]
        replace = []

        self.open_dialog(
            process_translate_text(
                self.session,
                key,
                replace,
            ),
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def cleanup(self) -> None:
        theme = get_theme()
        theme.background_color = BACKGROUND_COLOR
        theme.widget_font_color = FONT_COLOR
        theme.widget_font_shadow_color = (192, 192, 192)

    def open_dialog(
        self,
        pages: Sequence[str],
    ) -> None:
        logger.info("Opening dialog window")
        open_dialog(self.session, pages)
