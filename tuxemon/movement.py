# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PathfindNode:
    """Used in path finding search."""

    def __init__(
        self,
        value: tuple[int, int],
        parent: Optional[PathfindNode] = None,
    ) -> None:
        self.parent = parent
        self.value = value
        if self.parent:
            self.depth: int = self.parent.depth + 1
        else:
            self.depth = 0

    def get_parent(self) -> Optional[PathfindNode]:
        return self.parent

    def set_parent(self, parent: PathfindNode) -> None:
        self.parent = parent
        self.depth = parent.depth + 1

    def get_value(self) -> tuple[int, int]:
        return self.value

    def get_depth(self) -> int:
        return self.depth

    def __str__(self) -> str:
        s = str(self.value)
        if self.parent is not None:
            s += str(self.parent)
        return s
