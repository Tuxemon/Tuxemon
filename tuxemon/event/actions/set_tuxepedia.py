# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetTuxepediaAction(EventAction):
    """
    Set the key and value in the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            set_tuxepedia <character>,<monster_slug>,<label>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        monster_slug: Monster slug name (e.g. "rockitten").
        label: seen / caught
    """

    name = "set_tuxepedia"
    character: str
    monster_slug: str
    label: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return
        # start tuxepedia operations
        if self.label not in list(SeenStatus):
            raise ValueError(f"{self.label} isn't among {list(SeenStatus)}")
        label = SeenStatus(self.label)

        if self.monster_slug not in db.database["monster"]:
            raise ValueError(f"{self.monster_slug} isn't a monster")

        monster_name = T.translate(self.monster_slug)

        if label == SeenStatus.SEEN:
            character.tuxepedia.register_seen(self.monster_slug)
        elif label == SeenStatus.CAUGHT:
            character.tuxepedia.register_caught(self.monster_slug)

        logger.info(f"Tuxepedia: {monster_name} is registered as {label}!")
