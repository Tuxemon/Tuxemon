# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.entity.dialogue_profile import DialogueProfileManager
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session
from tuxemon.tools import open_dialog
from tuxemon.ui.text_formatter import TextFormatter

logger = logging.getLogger(__name__)


@final
@dataclass
class CharTalkAction(EventAction):
    """
    Displays dialogue for a character based on context and location.

    This action retrieves dialogue from the character's dialogue profile,
    optionally using a location-specific override. The dialogue field determines
    which type of line to display (e.g. greeting, pre_battle, farewell).

    Script usage:
        .. code-block::

            char_talk <character>,<field>[,location]

    Script parameters:
        character: Either "player" or the slug of an NPC (e.g. "npc_maple").
        field: The dialogue type to display. Must be one of:
            - greeting
            - idle
            - farewell
            - pre_battle
            - post_battle_win
            - post_battle_lose
            - post_battle_draw
        location: Optional map identifier (e.g. "map.tmx") used to override default dialogue.

    Behavior:
        - If a location is provided and a location-based override exists, it will be used.
        - Otherwise, the default dialogue profile is used.
        - If the dialogue field contains multiple lines, one is selected randomly.
        - Dialogue text is formatted before display.

    Example:
        char_talk npc_maple,greeting,map_forest
    """

    name = "char_talk"
    character: str
    field: str
    location: str | None = None

    def start(self, session: Session) -> None:
        character = session.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        dialogue = DialogueProfileManager()
        content = dialogue.get_npc_dialogue_content(
            character.slug, self.location
        )
        line = dialogue.get_dialogue_line(content, self.field)

        if line is None:
            logger.error(f"{self.character} line {self.field} doesn't exist.")
            self.stop()
            return

        text = TextFormatter.replace_text(session, line, T)
        open_dialog(client=session.client, text=[T.translate(text)])

    def update(self, session: Session, dt: float) -> None:
        if "DialogState" not in session.client.active_state_names:
            self.stop()
