# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence

from tuxemon.constants.paths import CORE_CONDITION_PATH, CORE_EFFECT_PATH
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import CoreEffect
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.db import LogicCondition, ParameterizableRule
from tuxemon.plugin import PluginObject


class CoreAssetManager:
    def __init__(self) -> None:
        self.effect_manager = EffectManager(
            CoreEffect,
            CORE_EFFECT_PATH,
        )
        self.condition_manager = ConditionManager(
            CoreCondition,
            CORE_CONDITION_PATH,
        )

    def parse_effects(
        self, data: Sequence[ParameterizableRule]
    ) -> Sequence[PluginObject]:
        return self.effect_manager.parse_effects(data) if data else []

    def parse_conditions(
        self, data: Sequence[LogicCondition]
    ) -> Sequence[PluginObject]:
        return self.condition_manager.parse_conditions(data) if data else []
