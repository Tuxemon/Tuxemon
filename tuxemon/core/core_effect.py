# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique


@dataclass
class EffectResult:
    name: str = ""
    success: bool = False
    extras: list[str] = field(default_factory=list)


@dataclass
class TechEffectResult(EffectResult):
    damage: int = 0
    element_multiplier: float = 0.0
    should_tackle: bool = False


@dataclass
class ItemEffectResult(EffectResult):
    num_shakes: int = 0


@dataclass
class StatusEffectResult(EffectResult):
    statuses: list[Status] = field(default_factory=list)
    techniques: list[Technique] = field(default_factory=list)


@dataclass
class CoreEffect:
    name: ClassVar[str]

    def __post_init__(self) -> None:
        cast_dataclass_parameters(self)

    def apply_globally(self, session: Session) -> EffectResult:
        return EffectResult()

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        return TechEffectResult(name=tech.name)

    def apply_tech(
        self, session: Session, tech: Technique
    ) -> TechEffectResult:
        return TechEffectResult(name=tech.name)

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        return ItemEffectResult(name=item.name)

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        return ItemEffectResult(name=item.name)

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        return StatusEffectResult(name=status.name)

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        return StatusEffectResult(name=status.name)
