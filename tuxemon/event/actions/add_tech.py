# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


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
    power: Union[float, None] = None
    potency: Union[float, None] = None
    accuracy: Union[float, None] = None
    npc_slug: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player
        if self.npc_slug is None:
            trainer_slug = "player"
        else:
            trainer_slug = self.npc_slug
        trainer = get_npc(self.session, trainer_slug)
        assert trainer
        instance_id = uuid.UUID(
            player.game_variables[self.monster_id],
        )
        monster = trainer.find_monster_by_id(instance_id)
        if monster is None:
            logger.error(f"No monster found with instance_id {instance_id}")
            raise ValueError()
        tech = Technique()
        tech.load(self.technique)
        if self.power:
            if 0.0 <= self.power <= 3.0:
                tech.power = self.power
            else:
                logger.error(f"{self.power} must be between 0.0 and 3.0")
                raise ValueError()
        if self.potency:
            if 0.0 <= self.potency <= 1.0:
                tech.potency = self.potency
            else:
                logger.error(f"{self.potency} must be between 0.0 and 1.0")
                raise ValueError()
        if self.accuracy:
            if 0.0 <= self.accuracy <= 1.0:
                tech.accuracy = self.accuracy
            else:
                logger.error(f"{self.accuracy} must be between 0.0 and 1.0")
                raise ValueError()
        monster.learn(tech)
