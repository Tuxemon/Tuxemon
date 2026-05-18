# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class PathView:
    """
    A contributor-proof path abstraction.

    Invariant:
        - The NEXT waypoint is always the LAST element of _tiles.
        - Path grows toward the front; consumption pops from the end.
    """

    __slots__ = ("_tiles", "_consumed")

    def __init__(self, tiles: Iterable[tuple[int, int]]):
        self._tiles = list(tiles)
        self._consumed: list[tuple[int, int]] = []

    def next(self) -> tuple[int, int] | None:
        """Return the next waypoint without consuming it."""
        return self._tiles[-1] if self._tiles else None

    def consume(self) -> tuple[int, int] | None:
        """Consume and return the next waypoint."""
        if not self._tiles:
            return None
        tile = self._tiles.pop()
        self._consumed.append(tile)
        return tile

    def push(self, tile: tuple[int, int]) -> None:
        """Append a new waypoint as the next step."""
        self._tiles.append(tile)

    def prepend(self, tile: tuple[int, int]) -> None:
        """
        Insert a waypoint at the *start* of the path.
        This is used for dynamic rerouting.
        """
        self._tiles.insert(0, tile)

    def extend_reversed(self, tiles: Iterable[tuple[int, int]]) -> None:
        """Append a reversed sequence so the last element is the next waypoint."""
        seq = list(tiles)
        self._tiles.extend(reversed(seq))

    def peek(self, n: int = 0) -> tuple[int, int] | None:
        """
        Peek n steps ahead.
        n=0 → next waypoint
        n=1 → second next waypoint
        """
        idx = len(self._tiles) - 1 - n
        if idx < 0:
            return None
        return self._tiles[idx]

    def clear(self) -> None:
        """Remove all remaining waypoints."""
        self._tiles.clear()

    def replace_tail(self, tiles: Iterable[tuple[int, int]]) -> None:
        """Replace the remaining path with a new sequence."""
        self._tiles = list(tiles)

    def splice(self, tiles: Iterable[tuple[int, int]]) -> None:
        """
        Insert new waypoints so they become the next steps.
        Equivalent to replacing the tail but preserving the invariant.
        """
        seq = list(tiles)
        self._tiles.extend(reversed(seq))

    def to_list(self) -> list[tuple[int, int]]:
        """Return a copy of the path."""
        return list(self._tiles)

    def consumed(self) -> list[tuple[int, int]]:
        """Return consumed waypoints (debug only)."""
        return list(self._consumed)

    def __len__(self) -> int:
        return len(self._tiles)

    def __bool__(self) -> bool:
        return bool(self._tiles)

    def __iter__(self) -> Iterator[tuple[int, int]]:
        return iter(self._tiles)

    def __repr__(self) -> str:
        return f"PathView(next={self.next()}, len={len(self)})"


@dataclass
class PathExecutionState:
    """
    Tracks a single tile-to-tile movement transition.
    """

    origin: tuple[int, int] | None = None
    target: tuple[int, int] | None = None

    @property
    def in_progress(self) -> bool:
        return self.origin is not None and self.target is not None

    def reset(self) -> None:
        self.origin = None
        self.target = None
