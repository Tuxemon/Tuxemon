# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class CombatType(Enum):
    MONSTER = "monster"
    TRAINER = "trainer"
    HORDE = "horde"


class BattleMode(Enum):
    SINGLE = "single"
    DOUBLE = "double"


@dataclass
class CombatContext:
    session: Session
    teams: list[NPC]
    combat_type: CombatType
    battle_mode: BattleMode

    def _validate_team_count(self) -> None:
        if len(self.teams) > 2:
            logger.warning(
                f"Multi-team combat detected with {len(self.teams)} teams."
            )
            raise NotImplementedError(
                "Multi-team combat is not yet supported."
            )

    @property
    def is_single_battle(self) -> bool:
        return self.battle_mode is BattleMode.SINGLE

    @property
    def is_double_battle(self) -> bool:
        return self.battle_mode is BattleMode.DOUBLE
