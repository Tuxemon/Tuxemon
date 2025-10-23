# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import (
    CoreEffect,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.db import EffectPhase

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@dataclass
class SwapOutLockEffect(CoreEffect):
    """
    Used to block or unblock a target from being swapped.
    Can be temporary or persistent.
    Applied via techniques or statuses.
    """

    name = "swap_out_lock"
    action: str  # Expected: 'block' or 'unblock'
    method: str  # Expected: 'temporary' or 'persistent'
    until_status_gone: str

    def __post_init__(self) -> None:
        self.action = self.action.lower().strip()
        self.method = self.method.lower().strip()
        valid_actions = {"block", "unblock"}
        valid_methods = {"temporary", "persistent"}

        if self.action not in valid_actions:
            raise ValueError(
                f"Invalid action '{self.action}'. Expected one of: {valid_actions}"
            )
        if self.method not in valid_methods:
            raise ValueError(
                f"Invalid method '{self.method}'. Expected one of: {valid_methods}"
            )

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat_session = session.client.combat_session
        persistent = self.method == "persistent"

        if self.action == "block":
            combat_session.swap_tracker.block_swap(
                monster=target, reason=tech.slug, persistent=persistent
            )
            logger.debug(
                f"Blocked swap ({target.name}) via technique {tech.name}"
            )
        elif self.action == "unblock":
            combat_session.swap_tracker.unblock_swap(monster=target)
            logger.debug(
                f"Unblocked swap for {target.name} via technique {tech.name}"
            )

        return TechEffectResult(name=tech.name, success=True)

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host
        combat_session = session.client.combat_session
        persistent = self.method == "persistent"

        if status.has_phase(EffectPhase.PERFORM_STATUS):
            if self.action == "block":
                combat_session.swap_tracker.block_swap(
                    monster=host, reason=status.slug, persistent=persistent
                )
                logger.debug(
                    f"Blocked swap ({host.name}) via status {status.name}"
                )
            elif self.action == "unblock":
                combat_session.swap_tracker.unblock_swap(monster=host)
                logger.debug(
                    f"Unblocked swap for {host.name} via status {status.name}"
                )

        elif status.has_phase(EffectPhase.ON_END):
            if (
                self.action == "block"
                and self.until_status_gone.lower() == "true"
            ):
                combat_session.swap_tracker.unblock_swap(monster=host)
                logger.debug(
                    f"Effect {status.name} ended—unblocking {host.name} from swap-in due to until_status_gone",
                )

        return StatusEffectResult(name=status.name, success=True)
