# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetEnvironmentAction(EventAction):
    """
    Switch or unload the active battle environment.

    Script usage:
        .. code-block::

            set_environment [slug]

    Script parameters:
        slug: Optional. If provided, loads the environment slug from the
            database. If omitted, unloads the current environment.

    Examples:
        set_environment grass
        set_environment
    """

    name = "set_environment"
    slug: str | None = None

    def start(self, session: Session) -> None:
        if self.slug is None:
            session.client.environment_manager.unload_environment()
            logger.info("Environment unloaded via event action.")
            self.stop()
            return

        success = session.client.environment_manager.load_environment(
            self.slug
        )
        if success:
            logger.info(f"Environment '{self.slug}' successfully loaded.")
        else:
            if session.client.environment_manager.is_locked():
                self.stop()
                return
            logger.error(f"Failed to load environment '{self.slug}'.")
