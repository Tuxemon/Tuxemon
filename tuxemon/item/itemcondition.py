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
class ItemCondition:
    """
    ItemConditions are evaluated by items.

    ItemCondition subclasses implement "conditions" defined in Tuxemon items.
    All subclasses, at minimum, must implement the following:

    * The ItemCondition.test() method
    * A meaningful name, which must match the name in item file effects

    By populating the "valid_parameters" class attribute, subclasses
    will be assigned a "parameters" instance attribute that holds the
    parameters passed to the condition in the item file.  It is also used
    to check the syntax of conditions, by verifying the correct type and
    number of parameters passed.

    Parameters
    ==========

    Tuxemon supports type-checking of the parameters defined in the items.

    valid_parameters may be the following format (may change):

    (type, name)

    * the type may be any valid python type, or even a python class or function
    * type may be a single type, or a tuple of types
    * type, if a tuple, may include None to indicate the parameter is optional
    * name must be a valid python string

    After parsing the parameters of the Item, the parameter's value
    will be passed to the type constructor.

    Example types: str, int, float, Monster, NPC

    (int, "level")                => level must be an int
    ((int, float), "level")       => can be an int or float
    ((int, float, None), "level") => is optional

    (Monster, "monster_slug")   => a Monster instance will be created
    """

    name: ClassVar[str]
    session: Session = field(init=False, repr=False)
    _op: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._op = self._op
        self.session = local_session
        self.user = local_session.player
        cast_dataclass_parameters(self)

    def test(self, target: Monster) -> bool:
        """
        Return True if satisfied, or False if not.

        Parameters:
            target: The target of the item's use.

        """
        return True
