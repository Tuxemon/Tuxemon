# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)

OPTIONS: list[str] = ["visible", "hidden", "exist"]


@dataclass
class KennelCondition(EventCondition):
    """
    Check if a kennel is hidden, visible, or exists.

    Script usage:
        .. code-block::

            is kennel <character>,<kennel>,<option>

    Script parameters:
        character: The character to check (either "player" or an NPC slug
            name, e.g. "npc_maple").
        kennel: The name of the kennel to check.
        option: The expected visibility of the kennel ("hidden" or
            "visible") or existence of it ("exist").
    """

    name: ClassVar[str] = "kennel"
    character: str
    kennel: str
    option: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)

        if character is None:
            logger.error(f"{self.character} not found")
            return False

        if self.option == "visible":
            return character.monster_boxes.has_box(
                self.kennel, "monster"
            ) and not character.monster_boxes.is_box_hidden(
                self.kennel, "monster"
            )
        elif self.option == "hidden":
            return character.monster_boxes.has_box(
                self.kennel, "monster"
            ) and character.monster_boxes.is_box_hidden(self.kennel, "monster")
        elif self.option == "exist":
            return character.monster_boxes.has_box(self.kennel, "monster")
        else:
            logger.error(f"The option {self.option} must be among {OPTIONS}")
            return False
