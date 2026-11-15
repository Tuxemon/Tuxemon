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
class BoundaryMoveAction(EventAction):
    """
    Moves the current active boundary by the given delta values.

    Script usage:
        .. code-block::

            boundary_move  <boundary_name>[,dx:dy]

    Script parameters:
        boundary_name: Required. The name to assign to the boundary
        dx: The change in the x-coordinate.
        dy: The change in the y-coordinate.
    """

    name = "boundary_move"
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
        if len(parts) != 2:
            logger.warning(
                f"BoundaryMoveAction requires 2 values (dx:dy), got {len(parts)}."
            )
            self.stop()
            return

        try:
            dx, dy = (int(p) for p in parts)
        except ValueError:
            logger.warning(
                f"Invalid numeric values in boundary_move: {self.values}"
            )
            self.stop()
            return

        try:
            boundary.move(dx, dy)
            logger.debug(f"Boundary moved by dx={dx}, dy={dy}.")
        except Exception as e:
            logger.warning(
                f"Failed to move active boundary: {type(e).__name__}: {e}"
            )
