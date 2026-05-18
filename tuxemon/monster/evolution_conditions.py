# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.db import (
    GenderType,
    MonsterEvolutionItemModel,
    PartyConditionsModel,
)
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.entity.party import PartyHandler
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


def check_party_conditions(
    party_handler: PartyHandler, conditions_model: PartyConditionsModel
) -> bool:
    """
    Evaluates whether the player's party meets the specified evolution conditions.
    """
    conditions = []

    # Check party alignment
    if conditions_model.alignment is not None:
        alignment = party_handler.alignment
        conditions.append(alignment == conditions_model.alignment)

    # Check required monster slugs
    if conditions_model.monster_slugs is not None:
        slug_counts: dict[str, int] = {}
        for mon in party_handler.monsters:
            slug_counts[mon.slug] = slug_counts.get(mon.slug, 0) + 1

        for slug, required_count in conditions_model.monster_slugs.items():
            conditions.append(slug_counts.get(slug, 0) >= required_count)

    # Check required monster types
    if conditions_model.monster_types is not None:
        type_counts: dict[str, int] = {}
        for mon in party_handler.monsters:
            for t in mon.types.current:
                type_counts[t.slug] = type_counts.get(t.slug, 0) + 1
        for type_, required_count in conditions_model.monster_types.items():
            conditions.append(type_counts.get(type_, 0) >= required_count)

    # Check required genders
    if conditions_model.genders is not None:
        gender_counts: dict[GenderType, int] = {}
        for mon in party_handler.monsters:
            gender_counts[mon.gender] = gender_counts.get(mon.gender, 0) + 1
        for gender, required_count in conditions_model.genders.items():
            conditions.append(gender_counts.get(gender, 0) >= required_count)

    # Check party size
    if conditions_model.party_size is not None:
        conditions.append(
            party_handler.party_size >= conditions_model.party_size
        )

    # Check party level
    if conditions_model.party_level is not None:
        average = party_handler.level_average
        conditions.append(
            average is not None and average >= conditions_model.party_level
        )

    # Check party stages
    if conditions_model.party_stages is not None:
        stage_counts: dict[str, int] = {}
        for mon in party_handler.monsters:
            stage = mon.stage.value
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        for stage, required_count in conditions_model.party_stages.items():
            conditions.append(stage_counts.get(stage, 0) >= required_count)

    return all(conditions)


def check_simple_conditions(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    conditions: list[bool],
) -> None:
    """
    Checks simple, monster-only properties like level, gender, element,
    and acquisition.
    """
    if evolution_item.at_level is not None:
        conditions.append(
            compare(
                "greater_or_equal",
                monster.level,
                evolution_item.at_level,
            )
        )
    if evolution_item.gender is not None:
        conditions.append(evolution_item.gender == monster.gender)
    if evolution_item.element is not None:
        conditions.append(monster.has_type(evolution_item.element))
    if evolution_item.acquisition is not None:
        conditions.append(evolution_item.acquisition == monster.acquisition)


def check_location_items_moves(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    context: dict[str, bool],
    conditions: list[bool],
) -> None:
    """Checks environment, inventory, and moveset."""
    owner = monster.get_owner()

    # Location check
    if evolution_item.inside is not None:
        conditions.append(
            evolution_item.inside == context.get("map_inside", False)
        )

    # Tech/HM check
    if evolution_item.tech is not None:
        conditions.append(owner.party.has_tech(evolution_item.tech))

    # Moves check
    if evolution_item.moves:
        moves_slugs = {mov.slug for mov in monster.moves.get_moves()}
        conditions.extend(move in moves_slugs for move in evolution_item.moves)

    if evolution_item.held_item is not None:
        held_item = monster.held_item
        conditions.append(
            held_item is not None
            and held_item.slug == evolution_item.held_item
        )


def check_tastes(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    conditions: list[bool],
) -> None:
    """Checks the monster's cold/warm tastes."""
    if not evolution_item.tastes:
        return

    for taste_type, required_value in evolution_item.tastes.items():
        monster_taste = getattr(monster, f"taste_{taste_type}", None)
        conditions.append(monster_taste == required_value)


def check_stats(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    conditions: list[bool],
) -> None:
    """
    Checks if the monster's stats meet the evolution comparison conditions.
    """
    if evolution_item.stats is None:
        return

    stat1 = monster.return_stat(evolution_item.stats.stat_type)
    operator = evolution_item.stats.comparison

    if evolution_item.stats.target_stat is not None:
        stat2 = monster.return_stat(evolution_item.stats.target_stat)
    elif evolution_item.stats.target_value is not None:
        stat2 = evolution_item.stats.target_value
    else:
        raise ValueError(
            "StatsComparison must have either target_stat or target_value."
        )

    conditions.append(compare(operator.value, stat1, stat2))


def check_variables(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    conditions: list[bool],
) -> None:
    """Append checks for required game variable values from the owner."""
    if not evolution_item.variables:
        return
    owner = monster.get_owner()
    conditions.append(
        owner.variable_manager.check_conditions(evolution_item.variables)
    )


def check_bond(
    monster: Monster,
    evolution_item: MonsterEvolutionItemModel,
    conditions: list[bool],
) -> None:
    """
    Append a check comparing the monster's bond level against the required value.
    """
    if evolution_item.bond is None:
        return

    _operator = evolution_item.bond.comparison
    _value = evolution_item.bond.value
    _bond = monster.bond_handler.bond
    conditions.append(compare(_operator.value, _bond, _value))
