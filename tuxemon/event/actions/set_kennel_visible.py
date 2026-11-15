# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import KENNEL
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
    visible: str | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            self.stop()
            return

        kennel = self.kennel
        is_visible = parse_flag(self.visible)

        if kennel == KENNEL:
            raise ValueError(f"{kennel} cannot be made invisible.")
        if not character.monster_boxes.has_box(kennel, "monster"):
            self.stop()
            return

        try:
            character.monster_boxes.set_box_hidden(
                kennel, "monster", not is_visible
            )
            logger.info(
                f"Set kennel '{kennel}' visibility for {self.npc_slug}: "
                f"{'visible' if is_visible else 'hidden'}"
            )
        except ValueError as e:
            logger.error(str(e))
