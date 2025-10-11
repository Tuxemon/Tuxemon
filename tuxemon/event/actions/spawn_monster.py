# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, final
from uuid import UUID

from tuxemon import formula
from tuxemon.db import Acquisition, EvolutionStage, StatType
from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.taste import Taste
from tuxemon.time_handler import today_ordinal
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.session import Session

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

    def start(self, session: Session) -> None:
        player = session.player
        mother_id = UUID(player.game_variables.get("breeding_mother"))
        father_id = UUID(player.game_variables.get("breeding_father"))

        mother = get_monster_by_iid(
            session, mother_id
        ) or player.monster_boxes.get_monsters_by_iid(mother_id)
        if mother is None:
            logger.error(f"Mother {mother_id} not found.")
            return

        father = get_monster_by_iid(
            session, father_id
        ) or player.monster_boxes.get_monsters_by_iid(father_id)
        if father is None:
            logger.error(f"Father {father_id} not found.")
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
            basic_forms = [
                element.slug
                for element in seed.history
                if element.stage == EvolutionStage.basic
            ]
            if basic_forms:
                seed_slug = random.choice(basic_forms)

        level = (father.level + mother.level) // 2

        # Create a new child monster
        child = Monster.spawn_base(seed_slug, level)
        child.set_capture(today_ordinal())
        child.name = name
        child.set_acquisition(Acquisition.BRED)

        # Give the child a random move from the father
        father_moves = len(father.moves.current_moves)
        replace_tech = random.randrange(0, 2)
        random_move = father.moves.get_moves()[random.randrange(father_moves)]
        child.moves.replace_move(replace_tech, random_move)
        logger.debug(f"Move inherited from father: move='{random_move.slug}'")

        # Tastes
        taste_warm, taste_cold = _determine_tastes(mother, father)
        child.taste_warm = taste_warm
        child.taste_cold = taste_cold
        logger.debug(
            f"Taste inherited from parents: warm='{taste_warm}', cold='{taste_cold}'"
        )
        child.set_stats()
        child.mother_iid = mother_id
        child.father_iid = father_id

        # Add the child to the character's monsters
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        character.party.add_monster(child, len(character.monsters))

        # Display a message to the player
        msg = T.format("got_new_tuxemon", {"monster_name": child.name})
        open_dialog(session.client, [msg])

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("DialogState")
        except ValueError:
            self.stop()


def _determine_seed(mother: Monster, father: Monster) -> Monster:
    """
    Choose the genetic seed parent using a biologically inspired
    hierarchy with trace logging.
    """

    stage_order: dict[EvolutionStage, int] = {
        EvolutionStage.stage2: 3,
        EvolutionStage.stage1: 2,
        EvolutionStage.standalone: 1,
    }
    stage_mother = stage_order.get(mother.stage, 0)
    stage_father = stage_order.get(father.stage, 0)
    logger.debug(
        f"Evolution stage - Mother: {stage_mother}, Father: {stage_father}"
    )

    if stage_mother > stage_father:
        logger.debug("Seed chosen based on higher evolution stage: Mother")
        return mother
    elif stage_father > stage_mother:
        logger.debug("Seed chosen based on higher evolution stage: Father")
        return father

    stats_mother = sum(mother.return_stat(s) for s in StatType)
    stats_father = sum(father.return_stat(s) for s in StatType)
    logger.debug(
        f"Total stats - Mother: {stats_mother}, Father: {stats_father}"
    )

    if stats_mother > stats_father:
        logger.debug("Seed chosen based on superior total stats: Mother")
        return mother
    elif stats_father > stats_mother:
        logger.debug("Seed chosen based on superior total stats: Father")
        return father

    vitality_mother = mother.hp_ratio
    vitality_father = father.hp_ratio
    logger.debug(
        "Vitality ratio "
        f"Mother: {vitality_mother:.2f}, Father: {vitality_father:.2f}"
    )

    if vitality_mother > vitality_father:
        logger.debug("Seed chosen based on greater vitality: Mother")
        return mother
    elif vitality_father > vitality_mother:
        logger.debug("Seed chosen based on greater vitality: Father")
        return father

    multiplier_mother = formula.calculate_multiplier(
        mother.types.current, father.types.current
    )
    multiplier_father = formula.calculate_multiplier(
        father.types.current, mother.types.current
    )
    logger.debug(
        "Type effectiveness "
        f"Mother vs Father: {multiplier_mother:.2f} "
        f"Father vs Mother: {multiplier_father:.2f}"
    )

    if multiplier_mother > multiplier_father:
        logger.debug("Seed chosen based on stronger type matchup: Mother")
        return mother
    elif multiplier_father > multiplier_mother:
        logger.debug("Seed chosen based on stronger type matchup: Father")
        return father

    logger.debug("Seed chosen randomly: No clear biological dominance")
    return random.choice([mother, father])


def _determine_tastes(mother: Monster, father: Monster) -> tuple[str, str]:
    """Taste inheritance for a Tuxemon offspring."""
    warm_slug = random.choice([mother.taste_warm, father.taste_warm])
    cold_slug = random.choice([mother.taste_cold, father.taste_cold])

    taste_warm = Taste.get_taste(warm_slug)
    taste_cold = Taste.get_taste(cold_slug)

    if not taste_warm:
        raise ValueError(
            f"Warm taste slug '{warm_slug}' could not be resolved."
        )

    if not taste_cold:
        raise ValueError(
            f"Cold taste slug '{cold_slug}' could not be resolved."
        )

    warm_slug = _mutate_taste(taste_warm, "warm")
    cold_slug = _mutate_taste(taste_cold, "cold")

    return (taste_warm.slug, taste_cold.slug)


def _mutate_taste(
    taste: Taste, taste_type: str, base_mutation: float = 0.3
) -> str:
    """
    Determines whether a taste should mutate, inversely scaled by rarity.
    Rare tastes are more stable, while common ones are more likely to mutate.
    """
    rarity = min(max(taste.rarity_score or 1.0, 0.0), 1.0)
    mutation_chance = base_mutation * rarity
    if random.random() < mutation_chance:
        new_slug = Taste.get_random_taste_excluding(
            taste_type,
            exclude_slugs=[taste.slug, "tasteless"],
            use_rarity=True,
        )
        if new_slug == taste.slug:
            logger.debug("Mutation selected same taste; skipping")
            return taste.slug
        if new_slug:
            logger.info(
                f"Taste '{taste.slug}' mutated to '{new_slug}' (chance: {mutation_chance:.2f})"
            )
            return new_slug
    return taste.slug


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
