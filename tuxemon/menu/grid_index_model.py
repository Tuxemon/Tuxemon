# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from tuxemon.menu.grid_layout import GridLayout

Orientation = Literal["horizontal", "vertical"]


@dataclass(frozen=True)
class GridIndexModel:
    """
    Grid layout semantics (horizontal orientation):

    VisualSpriteList arranges items in column-major order.

    Given:
        columns = C
        count = N
        rows = ceil(N / C)

    LR (left→right) index layout:
        0   1   2   ... C-1
        C  C+1 C+2 ... 2C-1
        ...

    Ragged grid example (N=8, C=3):
        0   1   2
        3   4   5
        6   7   _

    TB (top→bottom) index enumerates column by column:
        0   3   6
        1   4   7
        2   5   _

    Movement rules:
        - LR movement changes the column.
        - TB movement changes the row.
        - Ragged grids may have missing cells in the last row.

    Rectangular mode:
        - The grid is treated as full rows x columns.
        - Virtual cells exist for movement.
        - Movement wraps through the virtual grid.
        - After movement, the virtual index is mapped back to LR via modulo count.

    Vertical orientation:
        - LR/TB semantics are swapped.
        - Layout grows top→bottom first, then left→right.
        - Orientation remapping is applied before movement.

    These rules ensure consistent cursor movement and layout across:
        - horizontal vs vertical orientation
        - ragged vs rectangular grids
        - arbitrary item counts
    """

    count: int
    columns: int
    rectangular: bool
    orientation: Orientation
    layout: GridLayout = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", max(1, self.columns))
        layout = GridLayout(self.count, self.columns, self.rectangular)
        object.__setattr__(self, "layout", layout)

    def lr_to_tb(self, lr_index: int) -> int:
        return self.layout.lr_to_tb(lr_index, self.orientation)

    def tb_to_lr(self, tb_index: int) -> int:
        return self.layout.tb_to_lr(tb_index, self.orientation)

    def lr_to_rowcol(self, lr_index: int) -> tuple[int, int]:
        return self.layout.lr_to_rowcol(lr_index, self.orientation)

    def rowcol_to_lr(self, row: int, col: int) -> int:
        return row * self.columns + col

    def move_lr(self, lr_index: int, delta: int) -> int:
        if self.count == 0:
            return 0
        return (lr_index + delta) % self.count

    def move_tb(self, lr_index: int, delta: int) -> int:
        if self.count == 0:
            return 0
        tb = self.lr_to_tb(lr_index)
        tb = (tb + delta) % self.count
        return self.tb_to_lr(tb)

    def move(self, lr_index: int, index_type: str, delta: int) -> int:
        if index_type == "lr":
            return self.move_lr(lr_index, delta)
        else:
            return self.move_tb(lr_index, delta)

    def move_rectangular(
        self, lr_index: int, index_type: str, delta: int
    ) -> int:
        if self.count == 0:
            return 0

        rows = self.layout.rows
        cols = self.columns
        virtual_size = rows * cols

        # Orientation-aware remapping
        if self.orientation == "vertical":
            index_type = "tb" if index_type == "lr" else "lr"

        # Move in the virtual grid
        if index_type == "lr":
            virtual = (lr_index + delta) % virtual_size
        else:  # "tb"
            virtual = (lr_index + delta * cols) % virtual_size

        # Map back to real LR index
        return virtual % self.count
