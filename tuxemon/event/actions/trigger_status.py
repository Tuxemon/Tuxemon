# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final
from uuid import UUID

from tuxemon.db import EffectPhase
from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class TriggerStatusAction(EventAction):
    """
    Triggers the current status effect of a monster (e.g., poison, burn, sleep).

    Script usage:
        .. code-block::

            trigger_status <variable>,<status_name>

    Script parameters:
        variable: Name of the variable containing the monster ID. If not specified,
            all monsters in the party will be affected.
        status_name: Optional. If provided, only triggers the status effect if it matches
            the monster's current status slug.

    Examples:
        "trigger_status name_variable,poison"
        "trigger_status name_variable"
        "trigger_status"
    """

    name = "trigger_status"
    variable: str | None = None
    status_name: str | None = None

    def start(self, session: Session) -> None:
        player = session.player

        if self.variable is not None:
            variable = self.variable
            if not player.game_variables.has(variable):
                self.stop()
                return

            monster_id = UUID(player.game_variables.get(variable))
            monster = session.client.get_monster_by_iid(
                monster_id
            ) or player.monster_boxes.get_monsters_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                self.stop()
                return
            monsters = [monster]
        else:
            monsters = player.monsters

        if not monsters:
            self.stop()
            return

        monsters_with_status = [
            m for m in monsters if m.status.current_status is not None
        ]
        if not monsters_with_status:
            self.stop()
            return

        for monster in monsters_with_status:
            status = monster.status.current_status
            if status is None:
                continue

            if self.status_name is None or status.slug == self.status_name:
                status.use(session, EffectPhase.PERFORM_STATUS)
