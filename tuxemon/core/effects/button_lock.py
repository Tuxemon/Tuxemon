# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class ButtonLockEffect(CoreEffect):
    """
    Dynamically enables or disables specific menu options during combat.

    **Parameters**

    - ``menu``: The name of the menu option affected.
    - ``visible``: Whether the menu option should be enabled (``"true"``) or disabled (``"false"``).

    **Example**

    .. code-block:: json

        "effects": [
            "button_lock flee false"
        ]
    """

    name = "button_lock"
    menu: str
    visible: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = session.client.combat_session
        visible = self.visible.lower() == "true"

        if combat.menu_visibility_map:
            combat.menu_visibility_map[self.menu] = visible

        return TechEffectResult(name=tech.name, success=True)
