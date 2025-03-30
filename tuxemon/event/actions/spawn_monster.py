# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import re
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.states.dialog import DialogState
from tuxemon.time_handler import today_ordinal
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class SpawnMonsterAction(EventAction):
    """
    Breed a new monster.

    Add a new monster, created by breeding the two
    given mons (identified by instance_id, stored in a
    variable) and adds it to the given character's party
    (identified by slug). The parents must be in either
    the trainer's party, or a storage box owned by the
    trainer.

    Script usage:
        .. code-block::

            spawn_monster [npc_slug]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
            the one who is going to receive the new born

    """

    name = "spawn_monster"
    character: str

    def start(self) -> None:
        player = self.session.player
        mother_id = uuid.UUID(player.game_variables["breeding_mother"])
        father_id = uuid.UUID(player.game_variables["breeding_father"])

        mother = get_monster_by_iid(
            self.session, mother_id
        ) or player.monster_boxes.get_monsters_by_iid(mother_id)
        if mother is None:
            logger.debug(f"Mother {mother_id} not found.")
            return

        father = get_monster_by_iid(
            self.session, father_id
        ) or player.monster_boxes.get_monsters_by_iid(father_id)
        if father is None:
            logger.debug(f"Father {father_id} not found.")
            return

        # Determine the seed monster based on the types of the mother and father
        seed = _determine_seed(mother, father)
        if seed == father:
            name = _determine_name(father.name, mother.name)
        else:
            name = _determine_name(mother.name, father.name)

        # Get the basic form of the seed monster
        seed_slug = seed.slug
        if seed.history:
            seed_slug = next(
                (
                    element.mon_slug
                    for element in seed.history
                    if element.evo_stage.basic
                ),
                seed_slug,
            )

        level = (father.level + mother.level) // 2

        # Create a new child monster
        child = Monster()
        child.load_from_db(seed_slug)
        child.set_level(level)
        child.set_moves(level)
        child.set_capture(today_ordinal())
        child.name = name
        child.current_hp = child.hp

        # Give the child a random move from the father
        father_moves = len(father.moves)
        replace_tech = random.randrange(0, 2)
        child.moves[replace_tech] = father.moves[
            random.randrange(0, father_moves - 1)
        ]

        # Add the child to the character's monsters
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        character.add_monster(child, len(character.monsters))

        # Display a message to the player
        msg = T.format("got_new_tuxemon", {"monster_name": child.name})
        open_dialog(self.session, [msg])

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()


def _determine_seed(mother: Monster, father: Monster) -> Monster:
    """Determine the seed monster based on the multiplier."""

    mother_multiplier = formula.calculate_multiplier(
        mother.types, father.types
    )
    father_multiplier = formula.calculate_multiplier(
        father.types, mother.types
    )

    if mother_multiplier > father_multiplier:
        return mother
    elif father_multiplier > mother_multiplier:
        return father
    else:
        return random.choice([father, mother])


def _determine_name(first: str, second: str) -> str:
    """Combine two names by cutting each at the closest vocal."""

    if not re.search(r"[aeiouy]", first) or not re.search(r"[aeiouy]", second):
        # If either word doesn't have a vowel, split at the midpoint
        midpoint1 = len(first) // 2
        midpoint2 = len(second) // 2
        _first = first[:midpoint1]
        _second = second[midpoint2:]
        result = _first + _second
    else:
        # If both words have vowels, use the original algorithm
        def find_closest_vocal(word: str) -> int:
            midpoint = len(word) // 2
            min_distance = float("inf")
            closest_index = 0
            for i, char in enumerate(word):
                if char in "aeiouy":
                    distance = abs(i - midpoint)
                    if distance < min_distance:
                        min_distance = distance
                        closest_index = i
            return closest_index

        vocal_index1 = find_closest_vocal(first)
        vocal_index2 = find_closest_vocal(second)

        _first = first[: vocal_index1 + 1]
        _second = second[vocal_index2:]

        result = _first + _second

    # Remove duplicate characters
    result = "".join(
        [j for i, j in enumerate(result) if i == 0 or j != result[i - 1]]
    )

    return result.capitalize()
