# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel, NpcModel
from tuxemon.entity.sheet import get_combat_sheet
from tuxemon.graphics import load_surface, scale_sprite
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.session import Session
from tuxemon.sprite import Sprite


def get_avatar(session: Session, avatar: str) -> Sprite | None:
    """
    Retrieves the avatar sprite of a monster or NPC.

    Parameters:
        session: Game session.
        avatar: The identifier of the avatar to be used.

    Returns:
        The sprite for the monster or NPC avatar, or None if not found.
    """
    scale_int = session.client.context.scale

    if avatar.isdigit():
        monster = session.player.monsters[int(avatar)]
        renderer = MonsterRenderer(monster, scale=scale_int)
        return renderer.get_sprite("front")

    if avatar in db.database.get("monster", {}):
        model = MonsterModel.lookup(avatar, db)

        if model.sprites is None:
            return None

        loader = SpriteLoader()
        handler = MonsterSpriteHandler(
            slug=model.slug,
            sheet_path=loader.resolve_path(model.sprites.sheet),
            front_rect=model.sprites.front_rect,
            back_rect=model.sprites.back_rect,
            menu1_rect=model.sprites.menu1_rect,
            menu2_rect=model.sprites.menu2_rect,
        )
        return handler.get_sprite("menu", scale=scale_int)

    if avatar in db.database.get("npc", {}):
        sheet = get_combat_sheet(NpcModel.lookup(avatar, db).template)
        sprite = load_surface(sheet.front())
        scale_sprite(sprite, 0.5)
        return sprite

    return None
