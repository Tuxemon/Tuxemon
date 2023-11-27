# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique


@final
@dataclass
class AddTechAction(EventAction):
    """
    Adds a tech to a specific monster.

    Script usage:
        .. code-block::

            add_tech <monster_id>,<technique>[,power][,potency][,accuracy][,npc_slug]

    Script parameters:
        monster_id: Id of the monster (name of the variable).
        technique: Slug of the technique (e.g. "bullet").
        power: Power between 0.0 and 3.0
        potency: Potency between 0.0 and 1.0
        accuracy: Accuracy between 0.0 and 1.0
        npc_slug: npc slug name (e.g. "npc_maple") - default "player"

    """

    name = "add_tech"
    monster_id: str
    technique: str
    power: Optional[float] = None
    potency: Optional[float] = None
    accuracy: Optional[float] = None
    npc_slug: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        trainer = get_npc(self.session, self.npc_slug)
        assert trainer
        instance_id = uuid.UUID(
            player.game_variables[self.monster_id],
        )
        monster = trainer.find_monster_by_id(instance_id)
        if monster is None:
            raise ValueError(
                f"No monster found with instance_id {instance_id}",
            )
        tech = Technique()
        tech.load(self.technique)
        if self.power:
            if 0.0 <= self.power <= 3.0:
                tech.power = self.power
            else:
                raise ValueError(
                    f"{self.power} must be between 0.0 and 3.0",
                )
        if self.potency:
            if 0.0 <= self.potency <= 1.0:
                tech.potency = self.potency
            else:
                raise ValueError(
                    f"{self.potency} must be between 0.0 and 1.0",
                )
        if self.accuracy:
            if 0.0 <= self.accuracy <= 1.0:
                tech.accuracy = self.accuracy
            else:
                raise ValueError(
                    f"{self.accuracy} must be between 0.0 and 1.0",
                )
        monster.learn(tech)
