# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import FlairModel
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.monster.sprite import Flair
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterFlairAction(EventAction):
    """
    Set or replace a monster's flair in a given category.

    Script usage:
        .. code-block::

            set_monster_flair <variable>,<category>,<flair>[,<sprite_type_1>:<sprite_type_2>:...]

    Script parameters:
        variable: Name of the variable that holds the monster's UUID.
        category: Category of the monster flair.
        flair: Name of the monster flair.
        sprite_type(s): Optional pipe-separated list of sprite types
            (e.g., front:menu01)

    Behavior:
        - If the category already has a flair, it will be replaced.
        - If the category is new, the flair will be added.
        - If sprite types are provided, the flair will only apply to those views.
    """

    name = "set_monster_flair"
    variable: str
    category: str
    flair: str
    sprite_type: str = ""

    def start(self, session: Session) -> None:
        player = session.player
        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return

        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.error("Monster not found")
            self.stop()
            return

        try:
            flair_model = FlairModel.lookup(self.flair, db)
        except RuntimeError as e:
            logger.error(str(e))
            self.stop()
            return

        sprite_types = (
            set(self.sprite_type.split(":"))
            if self.sprite_type
            else flair_model.sprite_type
        )

        category = self.category.strip().lower()

        monster.flairs[category] = Flair(
            category=category,
            slug=flair_model.slug,
            weight=flair_model.weight,
            layer=flair_model.layer,
            layer_order=flair_model.layer_order,
            x_offset=flair_model.x_offset or 0,
            y_offset=flair_model.y_offset or 0,
            sprite_type_override=flair_model.sprite_type_override,
            sprite_type=sprite_types,
            color=flair_model.color,
        )

        monster.flair_slugs.add(flair_model.slug)
        scale = session.client.context.scale
        renderer = MonsterRenderer(monster, scale)
        renderer.sprite_handler.refresh_flairs(monster.flairs)

        if sprite_types:
            for sprite_type in sprite_types:
                renderer.get_sprite(sprite_type)

        if category in monster.flairs:
            logger.info(
                f"Replaced flair in category '{category}' for {monster.name}"
            )
        else:
            logger.info(
                f"Added flair in category '{category}' for {monster.name}"
            )
