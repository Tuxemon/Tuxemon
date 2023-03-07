# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique


@final
@dataclass
class AddTechAction(EventAction):
    """
    Adds a tech to a specific monster.

    Script usage:
        .. code-block::

            add_tech <monster_id>,<technique>

    Script parameters:
        monster_id: Id of the monster (name of the variable).
        technique: Slug of the technique (e.g. "bullet").

    """

    name = "add_tech"
    monster_id: str
    technique: str

    def start(self) -> None:
        player = self.session.player
        instance_id = uuid.UUID(
            player.game_variables[self.monster_id],
        )
        monster = player.find_monster_by_id(instance_id)
        if monster is None:
            raise ValueError(
                f"No monster found with instance_id {instance_id}",
            )
        tech = Technique(self.technique)
        if tech is None:
            raise ValueError(
                f"No tech found with slug {self.technique}",
            )
        tech_slugs = []
        for ele in monster.moves:
            tech_slugs.append(ele.slug)
        if tech.slug not in tech_slugs:
            monster.learn(tech)
