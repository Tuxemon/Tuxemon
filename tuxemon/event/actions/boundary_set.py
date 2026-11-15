# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class BoundarySetAction(EventAction):
    """
    Sets or replaces the current boundary with a new one, or resets to default
    if no parameters are given.

    Script usage:
        .. code-block::

            boundary_set <boundary_name>[,shape][,values]

    Script parameters:
        boundary_name: Required. The name to assign to the boundary
            (e.g., "safe_zone", "event").
        shape: Optional. Either "rectangle" or "circle".
        values: Optional. A colon-separated string of integers:
            - For "rectangle": x0:x1:y0:y1
            - For "circle": cx:cy:radius
    """

    name = "boundary_set"
    boundary_name: str
    shape: str | None = None
    values: str | None = None

    def start(self, session: Session) -> None:
        checker = session.client.boundary

        if not self.shape and not self.values:
            checker.reset_to_default()
            logger.debug("Boundary reset to default.")
            self.stop()
            return

        if not self.shape or not self.values:
            logger.warning(
                "BoundarySetAction requires both shape and values, or neither."
            )
            self.stop()
            return

        parts = self.values.split(":")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            logger.warning(
                f"Invalid numeric values in boundary_set: {self.values}"
            )
            self.stop()
            return

        if self.shape == "rectangle" and len(nums) == 4:
            x0, x1, y0, y1 = nums
            checker.set_rectangular_boundary(
                self.boundary_name, x0, x1, y0, y1
            )

        elif self.shape == "circle" and len(nums) == 3:
            cx, cy, radius = nums
            checker.set_circular_boundary(self.boundary_name, (cx, cy), radius)

        else:
            logger.warning(
                f"Invalid shape or parameter count: {self.shape}, {self.values}"
            )
