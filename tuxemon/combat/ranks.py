# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Rank titles earned along a path (Ladder campaign); pure helpers."""

from __future__ import annotations

from collections.abc import Sequence


def parse_titles(text: str) -> list[str]:
    """Titles written 'Novice:Scribe:Sage' as a list; blanks dropped."""
    return [t.strip() for t in text.split(":") if t.strip()]


def parse_rank(value: object) -> int:
    """The rank stored in a game variable; absent or garbled means 0."""
    try:
        return max(0, int(str(value)))
    except (TypeError, ValueError):
        return 0


def raise_rank(current: int, cap: int) -> int:
    """One rung higher, never above the number of titles."""
    return min(current + 1, cap)


def reach_rank(current: int, target: int, cap: int) -> int:
    """At least `target` (a higher rank is kept), never above the cap."""
    return min(max(current, target), cap)


def title_for(titles: Sequence[str], rank: int) -> str | None:
    """The title of a rank (1 = first title); None below rank 1."""
    if rank < 1 or not titles:
        return None
    return titles[min(rank, len(titles)) - 1]
