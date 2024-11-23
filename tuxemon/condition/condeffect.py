# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class CondEffectResult:
    name: str
    success: bool
    conditions: list[Condition]
    techniques: list[Technique]
    extras: list[str]


@dataclass
class CondEffect:
    """
    CondEffect are executed by conditions.

    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.session = local_session
        cast_dataclass_parameters(self)

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=[],
            extras=[],
        )
