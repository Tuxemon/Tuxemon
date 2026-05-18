# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from tuxemon.database.runtime import db
from tuxemon.db import NpcModel
from tuxemon.entity.npc import NPC
from tuxemon.platform.const.sizes import PLAYER_NPC

if TYPE_CHECKING:
    from tuxemon.save_system.save_state import NPCState
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class Player(NPC):
    """Object for Players. WIP."""

    def __init__(
        self,
        npc_slug: str,
        npc_data: NpcModel,
        session: Session,
        instance_id: UUID | None = None,
    ) -> None:
        super().__init__(
            npc_slug=npc_slug,
            npc_data=npc_data,
            session=session,
            instance_id=instance_id,
        )
        self.is_player = True

    @classmethod
    def create(cls, session: Session, slug: str) -> Player:
        """
        Creates a new player using the NpcModel lookup.
        """
        npc_data = NpcModel.lookup(slug, db)
        player = cls(slug, npc_data, session)

        if not session.has_player():
            session.set_player(player)

        return player

    @classmethod
    def from_save(cls, session: Session, save_data: NPCState) -> Player:
        slug = save_data.player_slug or PLAYER_NPC
        npc_data = NpcModel.lookup(slug, db)

        player = cls(slug, npc_data, session)
        player.set_state(session, save_data)
        return player

    def set_state(self, session: Session, save_data: NPCState) -> None:
        super().set_state(session, save_data)
        self.is_player = True

    def update(self, dt: float) -> None:
        super().update(dt)
