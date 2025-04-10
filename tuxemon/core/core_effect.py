# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Union

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique


@dataclass
class EffectResult:
    name: str
    success: bool
    extras: list[str]


@dataclass
class TechEffectResult(EffectResult):
    damage: int
    element_multiplier: float
    should_tackle: bool


@dataclass
class ItemEffectResult(EffectResult):
    num_shakes: int


@dataclass
class StatusEffectResult(EffectResult):
    statuses: list[Status]
    techniques: list[Technique]


@dataclass
class Effect:
    name: ClassVar[str]
    session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.session = local_session
        cast_dataclass_parameters(self)

    def apply(self, *args: Any, **kwargs: Any) -> EffectResult:
        raise NotImplementedError(
            "This method should be implemented by subclasses"
        )


@dataclass
class TechEffect(Effect):
    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        return TechEffectResult(
            name=tech.name,
            success=True,
            extras=[],
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
        )


@dataclass
class ItemEffect(Effect):
    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        return ItemEffectResult(
            name=item.name,
            success=True,
            extras=[],
            num_shakes=0,
        )


@dataclass
class StatusEffect(Effect):
    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        return StatusEffectResult(
            name=status.name,
            success=True,
            extras=[],
            statuses=[],
            techniques=[],
        )
