# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
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

    name = "kennel"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        _character, kennel_name, option = condition.parameters[:3]
        character = get_npc(session, _character)

        if character is None:
            logger.error(f"{_character} not found")
            return False

        if option == "visible":
            return character.monster_boxes.has_box(
                kennel_name, "monster"
            ) and not character.monster_boxes.is_box_hidden(
                kennel_name, "monster"
            )
        elif option == "hidden":
            return character.monster_boxes.has_box(
                kennel_name, "monster"
            ) and character.monster_boxes.is_box_hidden(kennel_name, "monster")
        elif option == "exist":
            return character.monster_boxes.has_box(kennel_name, "monster")
        else:
            logger.error(f"The option {option} must be among {OPTIONS}")
            return False
