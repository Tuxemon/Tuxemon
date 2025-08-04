# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL
from tuxemon.states.pc_kennel import HIDDEN_LIST
from tuxemon.tools import parse_flag

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetKennelVisibleAction(EventAction):
    """
    Set a kennel's visibility state for a character.

    From hidden to visible:
        set_kennel_visible player,name_kennel,true

    From visible to hidden:
        set_kennel_visible player,name_kennel,false

    Script usage:
        .. code-block::

            set_kennel_visible <character>,<kennel>,<visible>

    Script parameters:
        character: Either "player" or NPC slug name (e.g. "npc_maple").
        kennel: Name of the kennel.
        visible: Optional string flag to set visibility.
            Accepts "true", "1", "yes" for visible (case-insensitive).
            Defaults to False when omitted or invalid.
    """

    name = "set_kennel_visible"
    npc_slug: str
    kennel: str
    visible: Optional[str] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        kennel = self.kennel
        is_visible = parse_flag(self.visible)

        if kennel == KENNEL:
            raise ValueError(f"{kennel} cannot be made invisible.")
        if not character.monster_boxes.has_box(kennel, "monster"):
            return

        if is_visible:
            HIDDEN_LIST.remove(kennel)
        else:
            HIDDEN_LIST.append(kennel) if kennel not in HIDDEN_LIST else None
