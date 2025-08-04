# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class ButtonLockEffect(CoreEffect):
    """
    Effect that modifies menu visibility in combat.
    This effect dynamically enables or disables specific menu options.

    Attributes:
        menu: The menu option affected.
        visible: Determines if the menu option is enabled ("true") or disabled ("false")
    """

    name = "button_lock"
    menu: str
    visible: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.get_combat_state()
        visible = self.visible.lower() == "true"
        combat._menu_visibility.update_visibility(self.menu, visible)
        return TechEffectResult(name=tech.name, success=True)
