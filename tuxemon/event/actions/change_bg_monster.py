# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.session import Session


@final
@dataclass
class ChangeBgMonsterAction(EventAction):
    """
    Displays a monster sprite over a background image, using the
    monster's front sprite extracted from its sprite sheet.

    Script usage:
        .. code-block::

            change_bg_monster <background>,<monster_slug>

    Script parameters:
        background: The background identifier, which must be the name of
            a file located in `gfx/ui/background/` (without the `.png`
            extension). The background image must match the native
            resolution of the game (256x144 pixels).
        monster_slug: The slug of the monster to display. The monster
            must exist in the monster database. Its front sprite will be
            extracted from its sprite sheet and rendered on top of the
            background.

    Notes:
        - Background images must be located in `gfx/ui/background/`.
        - Background dimensions must be exactly 256x144 pixels.
        - The monster sprite is taken from the monster's sprite sheet
          using the `front_rect` defined in its model.
        - This action always pushes the `MonsterImageState`, which
          displays the background and overlays the monster sprite.
    """

    name = "change_bg_monster"
    background: str
    slug: str

    def start(self, session: Session) -> None:
        client = session.client

        if client.current_state is None:
            raise RuntimeError

        if client.has_extra_states():
            client.pop_state()

        if self.slug not in db.database["monster"]:
            raise ValueError(f"Monster {self.slug} not found")

        model = MonsterModel.lookup(self.slug, db)
        sprites = model.sprites
        assert sprites
        loader = SpriteLoader()

        handler = MonsterSpriteHandler(
            slug=model.slug,
            sheet_path=loader.resolve_path(sprites.sheet),
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
        )

        scale_int = session.client.context.scale
        sprite = handler.get_sprite("front", scale_int)

        client.push_state(
            "MonsterImageState",
            background=self.background,
            surface=sprite.image,
        )
