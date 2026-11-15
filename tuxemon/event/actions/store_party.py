# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import KENNEL
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class StorePartyAction(EventAction):
    """
    Store the entire party in a box.

    Save all monsters from the character's party into the named storage box,
    removing them from the party if successful.

    Script usage:
        .. code-block::

            store_party <character>[,box]

    Script parameters:
        character: Either "player" or an NPC slug (e.g. "npc_maple").
        box: An existing box where the monsters will be stored.
            If omitted, defaults to KENNEL.
    """

    name = "store_party"
    character: str
    box: str | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found.")
            self.stop()
            return

        store = self.box or KENNEL
        if self.box and not character.monster_boxes.has_box(store, "monster"):
            logger.error(f"No box found with name '{store}'.")
            self.stop()
            return

        success = character.monster_boxes.store_party_in_box(
            store, character.party.monsters
        )
        if not success:
            logger.error(
                f"Failed to store party in box '{store}': not enough space."
            )
        else:
            character.party.clear_party()
            logger.info(f"Party successfully stored in box '{store}'.")
