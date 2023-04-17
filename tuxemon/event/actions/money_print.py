# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class MoneyPrintAction(EventAction):
    """
    Print the current value of money dictionary to the console.

    If no entity is specified, print out values of all money dictionary.

    Script usage:
        .. code-block::

            money_print
            money_print <slug>

        Script parameters:
            slug: Slug name (e.g. player or NPC, etc.).

    """

    name = "money_print"
    slug: Optional[str] = None

    def start(self) -> None:
        var = self.session.player.money

        slug = self.slug
        if slug:
            if slug in var:
                print(f"{slug}: {var[slug]}")
            else:
                print(f"'{slug}' is broke.")
        else:
            print(var)
