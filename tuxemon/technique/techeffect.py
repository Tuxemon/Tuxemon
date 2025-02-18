# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from tuxemon.session import Session, local_session
from tuxemon.tools import cast_dataclass_parameters

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class TechEffectResult:
    name: str
    success: bool
    damage: int
    element_multiplier: float
    should_tackle: bool
    extras: list[str]


@dataclass
class TechEffect:
    """TechEffects are executed by techniques.

    TechEffect subclasses implement "effects" defined in Tuxemon techniques.
    All subclasses, at minimum, must implement the following:

    * The TechEffect.apply() method
    * A meaningful name, which must match the name in technique file effects

    By populating the "valid_parameters" class attribute, subclasses
    will be assigned a "parameters" instance attribute that holds the
    parameters passed to the action in the technique file.  It is also used
    to check the syntax of effects, by verifying the correct type and
    number of parameters passed.

    Parameters
    ==========

    Tuxemon supports type-checking of the parameters defined in the techniques.

    valid_parameters may be the following format (may change):

    (type, name)

    * the type may be any valid python type, or even a python class or function
    * type may be a single type, or a tuple of types
    * type, if a tuple, may include None to indicate the parameter is optional
    * name must be a valid python string

    After parsing the parameters of the Technique, the parameter's value
    will be passed to the type constructor.

    Example types: str, int, float, Monster, NPC

    (int, "duration")                => duration must be an int
    ((int, float), "duration")       => can be an int or float
    ((int, float, None), "duration") => is optional

    (Monster, "monster_slug")   => a Monster instance will be created
    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.session = local_session
        cast_dataclass_parameters(self)

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
