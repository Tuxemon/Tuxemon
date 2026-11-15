# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.boundary import CircularBoundary, RectangularBoundary
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class BoundaryResizeAction(EventAction):
    """
    Resizes the current active boundary.

    Script usage:
        .. code-block::

            boundary_resize <boundary_name>[,values]

    Script parameters:
        boundary_name: Required. The name to assign to the boundary
            (e.g., "safe_zone", "event").
        values: A colon-separated string of integers:
            - For rectangle: dx:dy
            - For circle: delta
    """

    name = "boundary_resize"
    boundary_name: str
    values: str

    def start(self, session: Session) -> None:
        checker = session.client.boundary
        boundary = checker.boundaries.get(self.boundary_name)

        if boundary is None:
            logger.error(
                f"Boundary '{self.boundary_name}' not found. Cannot move."
            )
            self.stop()
            return

        parts = self.values.split(":")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            logger.warning(
                f"Invalid numeric values in boundary_resize: {self.values}"
            )
            self.stop()
            return

        if isinstance(boundary, RectangularBoundary):
            if len(nums) == 2:
                dx, dy = nums
                boundary.resize(dx, dy)
                logger.debug(
                    f"Rectangular boundary resized by dx={dx}, dy={dy}."
                )
            else:
                logger.warning(
                    f"Rectangular boundary resize requires 2 values (dx:dy), got {len(nums)}."
                )

        elif isinstance(boundary, CircularBoundary):
            if len(nums) == 1:
                delta = nums[0]
                try:
                    boundary.resize(delta)
                    logger.debug(
                        f"Circular boundary radius adjusted by {delta}."
                    )
                except ValueError as e:
                    logger.warning(f"Failed to resize circular boundary: {e}")
            else:
                logger.warning(
                    f"Circular boundary resize requires 1 value (delta), got {len(nums)}."
                )

        else:
            logger.warning(
                f"Cannot resize boundary of type {type(boundary).__name__}."
            )
