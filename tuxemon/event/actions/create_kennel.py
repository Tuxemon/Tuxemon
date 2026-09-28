# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.boxes import BoxMetadata
from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import MAX_KENNEL
from tuxemon.session import Session
from tuxemon.tools import parse_flag

logger = logging.getLogger(__name__)


@final
@dataclass
class CreateKennelAction(EventAction):
    """
    Creates a new kennel with optional metadata.

    It's advisable to create a msgid in the en_US PO file.

    msgid "kennel_name"
    msgstr "Kennel Name"

    Script usage:
        .. code-block::

            # Create a visible kennel with default capacity
            create_kennel player,my_kennel

            # Create a hidden kennel with capacity 20
            create_kennel player,my_kennel,true,20

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: Name of the kennel.
        hidden: Optional flag ("true"/"false", "1"/"0", "yes"/"no") for
            visibility.
        max_capacity: Optional integer for maximum capacity (defaults to
            MAX_KENNEL).
    """

    name = "create_kennel"
    npc_slug: str
    kennel: str
    hidden: str | None = None
    max_capacity: int | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            self.stop()
            return

        if not character.monster_boxes.has_box(self.kennel, "monster"):
            capacity = (
                self.max_capacity
                if self.max_capacity is not None
                else MAX_KENNEL
            )
            is_hidden = parse_flag(self.hidden)

            metadata = BoxMetadata(max_capacity=capacity, is_hidden=is_hidden)
            character.monster_boxes.create_box(self.kennel, metadata)
            logger.info(
                f"Created kennel '{self.kennel}' for {self.npc_slug} "
                f"(capacity={capacity}, hidden={is_hidden})"
            )
