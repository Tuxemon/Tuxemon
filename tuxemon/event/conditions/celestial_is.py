# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CelestialIsCondition(EventCondition):
    """
    Evaluates a comparison against the current phase of a celestial body
    (e.g., moon, sun) as provided by the session's CelestialManager.

    This allows scripts to react to fictional astronomical cycles defined
    in `celestial_cycles.yaml`, such as checking whether the moon is full,
    waxing, waning, etc.

    Script usage:
        .. code-block::

            is celestial_is <body>,<operation>,<phase>

    Script parameters:
        body:
            The name of the celestial body to evaluate. This must match one
            of the cycle names defined in `celestial_cycles.yaml`, such as
            "moon" or "sun".

        operation:
            A comparison operator. Only string-based comparisons are valid
            for celestial phases:
            - "equals" or "=="
            - "not_equals" or "!="

        phase:
            The expected phase name to compare against. This must match one
            of the phase labels defined for the celestial body in the YAML
            configuration.

    Examples:
        .. code-block::

            is celestial_is moon,equals,full
            is celestial_is moon,not_equals,new
            is celestial_is sun,equals,high
    """

    name: ClassVar[str] = "celestial_is"
    body: str
    operation: str
    phase: str

    def test(self, session: Session) -> bool:

        try:
            current_phase = session.celestial.get_phase(self.body)
        except KeyError:
            logger.error(f"Unknown celestial body '{self.body}'")
            return False

        # Only string comparisons make sense for celestial phases
        if self.operation in ("equals", "=="):
            return current_phase == self.phase

        if self.operation in ("not_equals", "!="):
            return current_phase != self.phase

        logger.error(
            f"Operation '{self.operation}' not valid for celestial phases "
            f"(only equals / not_equals supported)"
        )
        return False
