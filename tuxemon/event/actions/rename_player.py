# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.platform.const.sizes import PLAYER_NAME_LIMIT

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RenamePlayerAction(EventAction):
    """
    Open the text input screen to rename the character.

    Script usage:
        .. code-block::

            rename_player <character> [random]

    Script parameters:
        character: Either "player" or an NPC slug (e.g. "npc_maple")
        random: Adding "random" makes appear the dontcare button in the input.
    """

    name = "rename_player"
    character: str
    random: str | None = None

    def set_player_name(self, char: NPC, name: str) -> None:
        char.name = name

    def start(self, session: Session) -> None:
        character = session.get_npc(self.character)

        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        session.client.push_state(
            "InputMenu",
            prompt=T.translate("input_name"),
            callback=partial(self.set_player_name, character),
            escape_key_exits=False,
            initial=session.player.name,
            char_limit=PLAYER_NAME_LIMIT,
            random=bool(self.random),
        )

    def update(self, session: Session, dt: float) -> None:
        if "InputMenu" not in session.client.active_state_names:
            self.stop()
