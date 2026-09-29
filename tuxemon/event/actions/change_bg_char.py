# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import NpcModel
from tuxemon.entity.sheet import get_combat_sheet
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import load_surface, scale_surface
from tuxemon.session import Session


@final
@dataclass
class ChangeBgNpcAction(EventAction):
    """
    Displays an NPC sprite over a background image, using the NPC's base
    sprite located in ``gfx/sprites/player/<slug>.png``.

    Script usage:
        .. code-block::

            change_bg_char <background>,<npc_slug>

    Script parameters:
        background:
            The background identifier, which must be the name of a file
            located in ``gfx/ui/background/`` (without the ``.png``
            extension). The background image must match the native
            resolution of the game (256x144 pixels).

        npc_slug:
            The slug of the NPC to display. A matching sprite file must
            exist at:

                ``gfx/sprites/player/<npc_slug>.png``

            The sprite will be loaded, scaled, and rendered on top of
            the background.

    Notes:
        - Background images must be located in ``gfx/ui/background/``.
        - Background dimensions must be exactly 256x144 pixels.
        - NPC sprites are loaded directly from their corresponding PNG
          file in ``gfx/sprites/player/``.
        - This action always pushes the ``NpcImageState``, which displays
          the background and overlays the NPC sprite.
    """

    name = "change_bg_char"
    background: str
    slug: str

    def start(self, session: Session) -> None:
        client = session.client

        if client.current_state is None:
            raise RuntimeError

        if client.has_extra_states():
            client.pop_state()

        if self.slug not in db.database["npc"]:
            raise ValueError(f"NPC {self.slug} not found")

        npc_data = NpcModel.lookup(self.slug, db)
        sheet = get_combat_sheet(npc_data.template)
        surface = sheet.front()
        scale_int = session.client.context.scale
        scaled = scale_surface(surface, scale_int)
        sprite = load_surface(scaled)

        client.push_state(
            "NpcImageState",
            background=self.background,
            surface=sprite.image,
        )
