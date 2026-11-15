# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from itertools import chain
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


class FieldMonsters:
    def __init__(self) -> None:
        self.monsters_in_play: defaultdict[NPC, list[Monster]] = defaultdict(
            list
        )

    @property
    def active_monsters(self) -> Sequence[Monster]:
        """List of all non-defeated monsters on the battlefield."""
        return list(chain.from_iterable(self.monsters_in_play.values()))

    def add_monster(self, npc: NPC, monster: Monster) -> None:
        """Adds a monster to the given NPC's active roster."""
        self.monsters_in_play[npc].append(monster)

    def remove_monster(self, npc: NPC, monster: Monster) -> None:
        """Removes a specific monster from the given NPC's roster if present."""
        if monster in self.monsters_in_play[npc]:
            self.monsters_in_play[npc].remove(monster)

    def remove_npc(self, npc: NPC) -> None:
        """Removes all monsters associated with the given NPC."""
        if npc in self.monsters_in_play:
            del self.monsters_in_play[npc]

    def get_monsters(self, npc: NPC) -> list[Monster]:
        """Returns the list of active monsters for the given NPC."""
        return self.monsters_in_play.get(npc, [])

    def get_all_monsters(self) -> dict[NPC, list[Monster]]:
        """Returns a dictionary containing all NPCs and their active monsters."""
        return self.monsters_in_play

    def get_npc_for_monster(self, monster: Monster) -> NPC:
        """Returns the NPC that controls the given monster, or Raise if not found."""
        for npc, monsters in self.monsters_in_play.items():
            if monster in monsters:
                return npc
        raise ValueError(f"Monster '{monster}' not found in any NPC's roster.")

    def clear_all(self) -> None:
        """Removes all NPCs and their monsters from play."""
        self.monsters_in_play.clear()
