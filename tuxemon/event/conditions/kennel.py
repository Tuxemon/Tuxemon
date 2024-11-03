# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.states.pc_kennel import HIDDEN_LIST

logger = logging.getLogger(__name__)

OPTIONS: list[str] = ["visible", "hidden", "exist"]


class KennelCondition(EventCondition):
    """
    Check if a kennel is hidden or visible.

    Script usage:
        .. code-block::

            is kennel <character>,<kennel>,<option>

    Script parameters:
        character: The character to check (either "player" or an NPC slug
            name, e.g. "npc_maple").
        kennel: The name of the kennel to check.
        option: The expected visibility of the kennel ("hidden" or
            "visible") or existence of it ("exist").

    Note: This condition checks if the kennel is in the HIDDEN_LIST. If the
        kennel is in the list, it is considered hidden; otherwise, it is
        considered visible.

    """

    name = "kennel"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, kennel_name, option = condition.parameters[:3]
        character = get_npc(session, _character)

        if character is None:
            logger.error(f"{_character} not found")
            return False
        if option == "visible":
            return kennel_name not in HIDDEN_LIST
        elif option == "hidden":
            return kennel_name in HIDDEN_LIST
        elif option == "exist":
            return character.monster_boxes.has_box(kennel_name, "monster")
        else:
            logger.error(f"The option {option} must be among {OPTIONS}")
            return False
