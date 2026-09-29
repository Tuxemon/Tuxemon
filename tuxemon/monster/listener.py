# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


def monster_update_listener(
    steps: float, monsters: list[Monster], session: Session, **kwargs: Any
) -> None:
    for monster in monsters:
        monster.steps += steps
        if monster.status:
            results = monster.status.tick_statuses_on_steps(session, steps)
            for r in results:
                logger.info(f"{monster.name} affected by {r.name}")
        if not monster.waiting_to_evolve:
            for evolution_item in monster.evolutions:
                if evolution_item.steps is not None:
                    if int(monster.steps) >= evolution_item.steps:
                        monster.waiting_to_evolve = True
                        break
