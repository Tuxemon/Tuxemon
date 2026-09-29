# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math

logger = logging.getLogger()


class GridLayout:
    """
    Computes grid geometry for VisualSpriteList.

    Handles:
    - ragged grids
    - rectangular grids
    - horizontal / vertical orientation

    This class is intentionally stateless and pure: it performs
    only mathematical transformations and never touches sprites.
    """

    def __init__(self, count: int, columns: int, rectangular: bool):
        self.count = count
        self.columns = max(1, columns)
        self.rectangular = rectangular

        if rectangular:
            # Full rectangular grid
            self.rows = math.ceil(count / self.columns)
            logger.debug(
                f"Rectangular grid: count={count}, columns={self.columns}, rows={self.rows}"
            )
        else:
            # Ragged grid
            self.rows, self.remainder = divmod(count, self.columns)
            logger.debug(
                f"Ragged grid: count={count}, columns={self.columns}, "
                f"rows={self.rows}, remainder={self.remainder}"
            )

    def lr_to_rowcol(self, lr_index: int, orientation: str) -> tuple[int, int]:
        """
        Convert LR index to (row, col) for layout.

        Horizontal:
            LR = row-major

        Vertical:
            - If columns == 1 → row-major
            - If columns > count → row-major
            - Otherwise → column-major with max column height = columns
        """
        if orientation == "horizontal":
            # Standard row-major
            row, col = divmod(lr_index, self.columns)
            return row, col

        # Single column → row-major
        if self.columns == 1:
            row = lr_index
            col = 0
            return row, col

        # More columns than items → row-major
        if self.columns > self.count:
            row = 0
            col = lr_index
            return row, col

        # Normal vertical mode → column-major with height = columns
        row = lr_index % self.columns
        col = lr_index // self.columns
        return row, col

    # ------------------------------------------------------------
    # LR → TB conversion
    # ------------------------------------------------------------
    def lr_to_tb(self, lr_index: int, orientation: str) -> int:
        logger.debug(f"LR→TB: lr_index={lr_index}, orientation={orientation}")
        if self.rectangular:
            row, col = divmod(lr_index, self.columns)
            if orientation == "horizontal":
                return col * self.rows + row
            else:
                return row * self.columns + col

        # Ragged grid
        row, col = divmod(lr_index, self.columns)

        if orientation == "horizontal":
            n_complete = min(col, self.remainder)
            n_incomplete = max(0, col - self.remainder)
            return (
                n_complete * (self.rows + 1) + n_incomplete * self.rows + row
            )
        else:
            n_complete = min(row, self.remainder)
            n_incomplete = max(0, row - self.remainder)
            return (
                n_complete * (self.rows + 1) + n_incomplete * self.rows + col
            )

    # ------------------------------------------------------------
    # TB → LR conversion
    # ------------------------------------------------------------
    def tb_to_lr(self, tb_index: int, orientation: str) -> int:
        logger.debug(f"TB→LR: tb_index={tb_index}, orientation={orientation}")
        if self.rectangular:
            if orientation == "horizontal":
                col, row = divmod(tb_index, self.rows)
                return row * self.columns + col
            else:
                row, col = divmod(tb_index, self.columns)
                return row * self.columns + col

        # Ragged grid
        if orientation == "horizontal":
            if tb_index < self.remainder * (self.rows + 1):
                col, row = divmod(tb_index, self.rows + 1)
            else:
                col, row = divmod(
                    tb_index - self.remainder * (self.rows + 1),
                    self.rows,
                )
                col += self.remainder
            return row * self.columns + col

        else:
            if tb_index < self.remainder * (self.rows + 1):
                row, col = divmod(tb_index, self.rows + 1)
            else:
                row, col = divmod(
                    tb_index - self.remainder * (self.rows + 1),
                    self.rows,
                )
                row += self.remainder
            return row * self.columns + col

    def __repr__(self) -> str:
        return (
            f"GridLayout(count={self.count}, columns={self.columns}, "
            f"rows={self.rows}, rectangular={self.rectangular})"
        )
