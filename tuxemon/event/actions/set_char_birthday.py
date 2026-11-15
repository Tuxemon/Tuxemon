# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.time_handler import random_month_day

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPlayerBirthdayAction(EventAction):
    """
    Open the date picker to set the player's birthday.

    Script usage:
        .. code-block::

            set_char_birthday <character> [random]

    Script parameters:
        character: Either "player" or an NPC slug (e.g. "npc_maple")
        random: If provided, assigns a random birthday instead of
            opening the date picker.
    """

    name = "set_char_birthday"
    character: str
    random: str | None = None

    def set_birthday(self, character: NPC, date: tuple[int, int]) -> None:
        character.birthdate = date
        logger.debug(f"Assigned birthday {date} to {character.slug}")

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)

        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        if self.random is not None:
            birthdate = random_month_day()
            self.set_birthday(character, birthdate)
            self.stop()
            self.stop()
            return

        session.client.push_state(
            "DatePickerState",
            callback=partial(self.set_birthday, character),
            escape_key_exits=False,
        )

    def update(self, session: Session, dt: float) -> None:
        if "DatePickerState" not in session.client.active_state_names:
            self.stop()
