# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetTemplateAction(EventAction):
    """
    Switch template (sprite and combat_front).

    Please remember that if you change the combat_front,
    automatically will change the combat_back.

    Eg if you put xxx, it's going to be xxx_back.png

    if you choose a feminine sprite, then it's advisable:
        heroine
    if you choose a masculine sprite, then it's advisable:
        adventurer

    Script usage:
        .. code-block::

            set_template <character>,<sprite>[,combat_front]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        sprite: must be inside mods/tuxemon/sprites (default = original)
        eg: adventurer_brown_back.png -> adventurer
        combat_front: must be inside mods/tuxemon/gfx/sprites/player
        eg: adventurer.png -> adventurer

    """

    name = "set_template"
    npc_slug: str
    sprite: str
    combat_front: Optional[str] = None

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        for template in npc.template:
            template.sprite_name = self.sprite
            if self.combat_front:
                template.combat_front = self.combat_front
        npc.load_sprites()
