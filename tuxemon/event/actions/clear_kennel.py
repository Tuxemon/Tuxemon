# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ClearKennelAction(EventAction):
    """
    Clear a kennel.

    It advisable to save the game and check twice.

    Remember the main kennel is "Kennel"

    Without destination (transfer) the monster will
    be deleted as well as the kennel.

    Script usage:
        .. code-block::

            clear_kennel <character>,<kennel>[,transfer]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: The kennel to clear.
        transfer: The kennel to transfer the monsters.
    """

    name = "clear_kennel"
    npc_slug: str
    kennel: str
    transfer: Optional[str] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        kennel = self.kennel
        transfer = self.transfer

        if kennel == KENNEL:
            raise ValueError(
                f"{kennel} cannot be cleared.",
            )
        else:
            if character.monster_boxes.has_box(kennel, "monster"):
                if transfer is None:
                    character.monster_boxes.remove_box(kennel)
                else:
                    character.monster_boxes.merge_boxes(kennel, transfer)
                    character.monster_boxes.remove_box(kennel)
            else:
                return
