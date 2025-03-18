# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique


@dataclass
class StatusEffectResult:
    name: str
    success: bool
    statuses: list[Status]
    techniques: list[Technique]
    extras: list[str]


@dataclass
class StatusEffect:
    """
    StatusEffect are executed by status.

    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.session = local_session
        cast_dataclass_parameters(self)

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=[],
            techniques=[],
            extras=[],
        )
