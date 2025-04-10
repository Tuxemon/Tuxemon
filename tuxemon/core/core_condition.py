# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@dataclass
class CoreCondition:
    """
    CoreCondition handles multiple condition types with operational state tracking via _op.
    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)
    # Represents truth state (is/not)
    _op: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.session = local_session
        self.player = self.session.player
        cast_dataclass_parameters(self)

    def test_with_monster(self, target: Monster) -> bool:
        """Test conditions related to a Monster's attributes."""
        logger.info(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_item(self, target: Item) -> bool:
        """Test conditions related to a Item's attributes."""
        logger.info(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_tech(self, target: Technique) -> bool:
        """Test conditions related to a Technique's attributes."""
        logger.info(f"Testing {target.name} for condition {self.name}")
        return True

    def test_with_status(self, target: Status) -> bool:
        """Test conditions related to a Status's attributes."""
        logger.info(f"Testing {target.name} for condition {self.name}")
        return True

    def test_multiple_targets(self, targets: list[Any]) -> bool:
        """
        Validate all conditions for multiple targets using the appropriate test methods.
        """
        if not targets:
            return False

        for target in targets:
            target_type = target.__class__.__name__.lower()
            test_method_name = f"test_with_{target_type}"

            try:
                test_method = getattr(self, test_method_name)
                if not test_method(target):
                    return False
            except AttributeError:
                logger.warning(
                    f"No test method found for target type: {target_type}"
                )
                return False
            except Exception as e:
                logger.error(f"Error while testing target {target_type}: {e}")
                return False

        return True
