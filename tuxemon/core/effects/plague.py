# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale import T
from tuxemon.monster_dir.plague import InfectionResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class PlagueEffect(CoreEffect):
    """
    Plague is an effect that can infect a monster with a specific disease,
    using a spreadness value defined in the external configuration file
    `plagues.yaml`.

    Attributes:
        plague_slug: The slug of the plague to apply. This is used to look up
            the plague's properties, such as spreadness, from the config.
    """

    name = "plague"
    plague_slug: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        result_code = target.plague.try_infect(target, self.plague_slug)
        success = result_code in (
            InfectionResult.INFECTED,
            InfectionResult.CARRIER,
        )
        extra = []
        plague_config = target.plague.get_plague_config(self.plague_slug)
        params = {"target": target.name.upper(), "user": user.name.upper()}

        if success:
            message_key = target.plague.get_combat_message_key(
                self.plague_slug
            )
            extra.append(T.format(message_key, params))

            if plague_config:
                msgid = (
                    plague_config.message_spread_success
                    or "combat_state_plague2"
                )
                tech.use_tech = T.translate(msgid)

        elif result_code == InfectionResult.MINOR_EFFECT:
            if plague_config and plague_config.message_minor_effect:
                extra.append(
                    T.format(plague_config.message_minor_effect, params)
                )

        else:  # 'resisted', 'immune', 'already_has', or a failed minor_effect
            message_key = target.plague.get_combat_message_key(
                self.plague_slug
            )
            extra.append(T.format(message_key, params))

        cured, message = target.plague.try_cure(target, self.plague_slug)
        if cured and message:
            extra.append(T.format(message, params))

        return TechEffectResult(name=tech.name, success=success, extras=extra)
