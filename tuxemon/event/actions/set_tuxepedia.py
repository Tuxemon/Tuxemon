# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import SeenStatus, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T

logger = logging.getLogger(__name__)


@final
@dataclass
class SetTuxepediaAction(EventAction):
    """
    Set the key and value in the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            set_tuxepedia <character>,<monster_slug>,<label>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        monster_slug: Monster slug name (e.g. "rockitten").
        label: seen / caught

    """

    name = "set_tuxepedia"
    character: str
    monster_slug: str
    label: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        # start tuxepedia operations
        tuxepedia = character.tuxepedia
        _seen = SeenStatus.seen
        _caught = SeenStatus.caught
        # check label
        if self.label not in list(SeenStatus):
            raise ValueError(f"{self.label} isn't among {list(SeenStatus)}")
        label = SeenStatus(self.label)
        # check if existing monster
        monsters = list(db.database["monster"])
        if self.monster_slug not in monsters:
            raise ValueError(f"{self.monster_slug} isn't a monster")
        # regroup monsters
        caught = [key for key, value in tuxepedia.items() if value == _caught]
        seen = [key for key, value in tuxepedia.items() if value == _seen]
        # append monster to tuxepedia
        monster = self.monster_slug
        name = T.translate(monster)
        if label == _caught and monster not in caught:
            logger.info(f"Tuxepedia: {name} is registered as {_caught}!")
            tuxepedia[monster] = label
        # avoid reset caught into seen
        if label == _seen and monster not in seen and monster not in caught:
            logger.info(f"Tuxepedia: {name} is registered as {_seen}!")
            tuxepedia[monster] = label
