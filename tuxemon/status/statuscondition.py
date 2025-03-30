# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@dataclass
class StatusCondition:
    """
    StatusCondition are evaluated by status.

    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)
    _op: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._op = self._op
        self.session = local_session
        self.player = local_session.player
        cast_dataclass_parameters(self)

    def test(self, target: Monster) -> bool:
        """
        Return True if satisfied, or False if not.

        """
        return True
