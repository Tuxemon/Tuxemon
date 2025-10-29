# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class QuarantineAction(EventAction):
    """
    Quarantine or release monsters infected with a specific plague.

    Usage:
        quarantine <character>,<plague_slug>,<value>[,amount]

    Parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        plague_slug: The slug of the plague to target.
        action_type: "in" to quarantine infected monsters, "out" to release them.
        amount: (Optional, only for "out") The number of monsters to release
            randomly.

    Example: "quarantine out,5" (Release 5 infected monsters randomly)
    """

    name = "quarantine"
    npc_slug: str
    plague_slug: str
    action_type: str
    amount: Optional[int] = None

    def _quarantine_in(self, character: NPC) -> None:
        """Moves currently infected monsters from the party into the quarantine box."""
        party = character.party
        boxes = character.monster_boxes

        if not boxes.has_box(self.name, "monster"):
            boxes.create_box(self.name, "monster")

        to_quarantine = [
            mon
            for mon in party.monsters
            if mon.plague.has_plague(self.plague_slug)
            and mon.plague.is_infected_with(self.plague_slug)
        ]

        for monster in to_quarantine:
            # Inoculates the monster before moving it.
            monster.plague.inoculate(self.plague_slug)

            if party.transfer_monster_to_box(monster, self.name):
                logger.info(f"{monster} has been quarantined")
            else:
                logger.warning(f"Failed to quarantine {monster}")

    def _quarantine_out(self, character: NPC) -> None:
        """Moves selected monsters from the quarantine box back to the party."""
        party = character.party
        boxes = character.monster_boxes

        if not boxes.has_box(self.name, "monster"):
            logger.info(f"Box {self.name} does not exist")
            return

        box_monsters = [
            mon
            for mon in boxes.get_monsters(self.name)
            if mon.plague.has_plague(self.plague_slug)
        ]

        if not box_monsters:
            logger.info(f"Box {self.name} is empty")
            return

        if self.amount is None or self.amount >= len(box_monsters):
            to_release = box_monsters
        else:
            to_release = random.sample(box_monsters, self.amount)

        for monster in to_release:
            # Inoculates the monster before releasing it.
            monster.plague.inoculate(self.plague_slug)

            if party.transfer_monster_to_party(monster):
                boxes.remove_monster_from(self.name, monster)
                logger.info(f"{monster} has been inoculated and released")
            else:
                logger.warning(f"Failed to release {monster} to party")

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        if self.action_type == "in":
            self._quarantine_in(character)

        elif self.action_type == "out":
            self._quarantine_out(character)

        else:
            raise ValueError(
                f"Value '{self.action_type}' must be 'in' or 'out'"
            )
