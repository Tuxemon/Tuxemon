# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from operator import eq, ge, gt, le, lt, ne
from typing import TYPE_CHECKING, Optional

from tuxemon.db import (
    ElementType,
    EvolutionStage,
    GenderType,
    MonsterShape,
    TasteCold,
    TasteWarm,
)
from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class ParkCondition(ItemCondition):
    """
    Park condition filters out specific conditions.

    It allows filtering: slug, gender, evolution_stage, element, shape,
    taste_warm, taste_cold, level, weight, height, max_hp, current_hp,
    armour, dodge, melee, ranged and speed.

    eg: park slug,xxx
    eg: park weight,less_than,100
    """

    name = "park"
    filter_name: str
    value_name: str
    extra: Optional[str] = None

    def test(self, target: Monster) -> bool:
        assert target
        filter_name = self.filter_name
        value_name = self.value_name
        result = False
        # filter slug
        if filter_name == "slug" and target.slug == value_name:
            result = True
        # filter genders
        if (
            filter_name == "gender"
            and value_name in list(GenderType)
            and target.gender == value_name
        ):
            result = True
        # filter evolution stages
        if (
            filter_name == "evolution_stage"
            and value_name in list(EvolutionStage)
            and target.stage == value_name
        ):
            result = True
        # filter element / type
        if (
            filter_name == "element"
            and value_name in list(ElementType)
            and target.has_type(ElementType(value_name))
        ):
            result = True
        # filter shape
        if (
            filter_name == "shape"
            and value_name in list(MonsterShape)
            and target.shape == value_name
        ):
            result = True
        # filter taste warm
        if (
            filter_name == "taste_warm"
            and value_name in list(TasteWarm)
            and target.taste_warm == value_name
        ):
            result = True
        # filter taste cold
        if (
            filter_name == "taste_cold"
            and value_name in list(TasteCold)
            and target.taste_cold == value_name
        ):
            result = True

        # filter numeric fields
        if self.extra is not None:
            field = 0
            if filter_name == "level":
                field = target.level
            elif filter_name == "weight":
                field = int(target.weight)
            elif filter_name == "height":
                field = int(target.height)
            elif filter_name == "max_hp":
                field = target.hp
            elif filter_name == "current_hp":
                field = target.current_hp
            elif filter_name == "armour":
                field = target.armour
            elif filter_name == "dodge":
                field = target.dodge
            elif filter_name == "melee":
                field = target.melee
            elif filter_name == "ranged":
                field = target.ranged
            elif filter_name == "speed":
                field = target.speed
            extra = int(self.extra)
            if value_name == "less_than" and bool(lt(field, extra)):
                result = True
            elif value_name == "less_or_equal" and bool(le(field, extra)):
                result = True
            elif value_name == "greater_than" and bool(gt(field, extra)):
                result = True
            elif value_name == "greater_or_equal" and bool(ge(field, extra)):
                result = True
            elif value_name == "equals" and bool(eq(field, extra)):
                result = True
            elif value_name == "not_equals" and bool(ne(field, extra)):
                result = True

        return result
