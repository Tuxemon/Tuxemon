# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class CreateKennelAction(EventAction):
    """
    Creates a new kennel.

    It's advisable to create a msgid in the en_US PO file.

    msgid "kennel_name"
    msgstr "Kennel Name"

    Script usage:
        .. code-block::

            create_kennel <character>,<kennel>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: Name of the kennel.
    """

    name = "create_kennel"
    npc_slug: str
    kennel: str

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        if not character.monster_boxes.has_box(self.kennel, "monster"):
            character.monster_boxes.create_box(self.kennel, "monster")
