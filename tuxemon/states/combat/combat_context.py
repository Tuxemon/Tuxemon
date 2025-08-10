# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.npc import NPC
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
    graphics: BattleGraphicsModel
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

    def get_start_message(self) -> str:
        """Determines and returns the appropriate alert message for combat start."""
        if self.combat_type is CombatType.TRAINER:
            params = {"name": self.teams[1].name.upper()}
            return T.format("combat_trainer_appeared", params)
        elif self.combat_type is CombatType.MONSTER:
            params = {"name": self.teams[1].monsters[0].name.upper()}
            return T.format("combat_wild_appeared", params)
        elif self.combat_type is CombatType.HORDE:
            return T.translate("combat_horde_appeared")
        else:
            raise ValueError(f"Unexpected combat_type: {self.combat_type}")

    @property
    def is_trainer_battle(self) -> bool:
        return self.combat_type is CombatType.TRAINER

    @property
    def is_monster_battle(self) -> bool:
        return self.combat_type is CombatType.MONSTER

    @property
    def is_horde_battle(self) -> bool:
        return self.combat_type is CombatType.HORDE

    @property
    def is_single_battle(self) -> bool:
        return self.battle_mode is BattleMode.SINGLE

    @property
    def is_double_battle(self) -> bool:
        return self.battle_mode is BattleMode.DOUBLE
