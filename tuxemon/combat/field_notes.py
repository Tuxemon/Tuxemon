# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
What the player has learned about the battle rules (field notes).

Type matchups:

A matchup (attack type, defending type) is learned the first time the player
sees a technique of that type hit a monster of that type, in any battle the
player takes part in. A dual-type target teaches both of its types. The
field-notes phone app shows only learned matchups, so the type chart fills in
as the player plays instead of being known up front.

Attack ranges (melee, touch, ranged, reach, reliable): learned the first time
a damaging technique of that range hits, used by or against the player.

Stored in the game variables ``known_matchups`` ("fire>wood,water>fire") and
``known_ranges`` ("melee,ranged"), so they are saved with the game and need
no save-format change.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC

KNOWN_MATCHUPS = "known_matchups"
KNOWN_RANGES = "known_ranges"
APP_SLUG = "app_field_notes"


def has_field_notes(character: NPC) -> bool:
    """Return True if the character carries the Field notes app."""
    return character.bag.has_item(APP_SLUG)


def known_matchups(character: NPC) -> set[tuple[str, str]]:
    """Return the (attack type, defending type) pairs the character knows."""
    raw = character.game_variables.get(KNOWN_MATCHUPS) or ""
    pairs = set()
    for entry in raw.split(","):
        attack, sep, defend = entry.partition(">")
        if sep and attack and defend:
            pairs.add((attack, defend))
    return pairs


def record_matchups(
    character: NPC,
    attack_types: Iterable[str],
    defend_types: Iterable[str],
) -> list[tuple[str, str]]:
    """
    Learn every pairing of the given attack and defending types.

    Returns:
        The newly learned pairs, sorted (empty if all were known).
    """
    known = known_matchups(character)
    defend = list(defend_types)
    new = sorted(
        {(a, d) for a in attack_types for d in defend} - known,
    )
    if new:
        known.update(new)
        character.game_variables.set(
            KNOWN_MATCHUPS, ",".join(f"{a}>{d}" for a, d in sorted(known))
        )
    return new


def known_ranges(character: NPC) -> set[str]:
    """Return the attack ranges the character knows."""
    raw = character.game_variables.get(KNOWN_RANGES) or ""
    return {r for r in raw.split(",") if r}


def record_range(character: NPC, attack_range: str) -> bool:
    """Learn an attack range. Returns True if it was new."""
    known = known_ranges(character)
    if not attack_range or attack_range in known:
        return False
    known.add(attack_range)
    character.game_variables.set(KNOWN_RANGES, ",".join(sorted(known)))
    return True


def learn_from_hit(
    character: NPC,
    attack_types: Iterable[str],
    defend_types: Iterable[str],
    attack_range: str,
) -> bool:
    """
    Record what a damaging hit teaches, if the character has the app.

    Returns:
        True if something new was learned (always False without the app).
    """
    if not has_field_notes(character):
        return False
    learned = bool(record_matchups(character, attack_types, defend_types))
    return record_range(character, attack_range) or learned
