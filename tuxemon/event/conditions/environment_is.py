# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class EnvironmentIsCondition(EventCondition):
    """
    Check that the currently active environment slug corresponds to the expected value.

    Script usage:
        .. code-block::

            is environment_is <slug>

    Script parameters:
        slug: The environment slug to check against the active environment.

    Examples:
        is environment_is grass
        is environment_is cave
    """

    name: ClassVar[str] = "environment_is"
    slug: str

    def test(self, session: Session) -> bool:
        env = session.client.environment_manager.get_active_environment()
        if env is None:
            return False
        return env.data.slug == self.slug
