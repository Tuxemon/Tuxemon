# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
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
        value: "in" to quarantine infected monsters, "out" to release them.
        amount: (Optional, only for "out") The number of monsters to release
            randomly.

    Example: "quarantine out,5" (Release 5 infected monsters randomly)
    """

    name = "quarantine"
    npc_slug: str
    plague_slug: str
    value: str
    amount: Optional[int] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        party = character.party
        boxes = character.monster_boxes

        if not boxes.has_box(self.name, "monster"):
            boxes.create_box(self.name, "monster")

        if self.value == "in":
            plague = [
                mon
                for mon in party.monsters
                if mon.plague.has_plague(self.plague_slug)
                and mon.plague.is_infected_with(self.plague_slug)
            ]
            for monster in plague:
                monster.plague.inoculate(self.plague_slug)
                if party.transfer_monster_to_box(monster, self.name):
                    logger.info(f"{monster} has been quarantined")
                else:
                    logger.warning(f"Failed to quarantine {monster}")

        elif self.value == "out":
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

            to_release = (
                box_monsters
                if self.amount is None or self.amount >= len(box_monsters)
                else random.sample(box_monsters, self.amount)
            )

            for monster in to_release:
                monster.plague.inoculate(self.plague_slug)
                if party.transfer_monster_to_party(monster):
                    boxes.remove_monster_from(self.name, monster)
                    logger.info(f"{monster} has been inoculated and released")
                else:
                    logger.warning(f"Failed to release {monster} to party")

        else:
            raise ValueError(f"{self.value} must be 'in' or 'out'")
