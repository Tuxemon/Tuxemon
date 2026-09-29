# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.session import Session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@dataclass
class CoreCondition:
    """
    CoreCondition handles multiple condition types with operational state
    tracking via is_expected.
    """

    name: ClassVar[str]
    # Represents truth state (is/not)
    is_expected: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        cast_dataclass_parameters(self)

    def test(self, session: Session) -> bool:
        """Test conditions."""
        return False

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        """Test conditions related to a Monster's attributes."""
        logger.debug(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_item(self, session: Session, target: Item) -> bool:
        """Test conditions related to a Item's attributes."""
        logger.debug(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_tech(self, session: Session, target: Technique) -> bool:
        """Test conditions related to a Technique's attributes."""
        logger.debug(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_status(self, session: Session, target: Status) -> bool:
        """Test conditions related to a Status's attributes."""
        logger.debug(f"Testing {target.name} for condition {self.name}")
        return True
