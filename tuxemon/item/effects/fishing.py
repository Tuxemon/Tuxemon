# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.db import EvolutionStage, MonsterShape, db
from tuxemon.event.actions.wild_encounter import WildEncounterAction
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class FishingEffectResult(ItemEffectResult):
    pass


@dataclass
class FishingEffect(ItemEffect):
    """This effect triggers fishing."""

    name = "fishing"
    value: str

    def apply(self, target: Monster) -> FishingEffectResult:
        # level of the rod
        levels = ["basic", "advanced", "pro"]
        if self.value not in levels:
            raise ValueError(f"{self.value} must be bas, adv or pro")

        # define random encounters
        bas = []
        adv = []
        pro = []
        monsters = list(db.database["monster"])
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                if results.stage == EvolutionStage.basic:
                    if (
                        results.shape == MonsterShape.polliwog
                        or results.shape == MonsterShape.aquatic
                    ):
                        bas.append(results.slug)
                if (
                    results.stage == EvolutionStage.stage1
                    or results.stage == EvolutionStage.basic
                ):
                    if (
                        results.shape == MonsterShape.polliwog
                        or results.shape == MonsterShape.aquatic
                    ):
                        adv.append(results.slug)
                if results.stage != EvolutionStage.basic:
                    if (
                        results.shape == MonsterShape.polliwog
                        or results.shape == MonsterShape.aquatic
                        or results.shape == MonsterShape.leviathan
                    ):
                        pro.append(results.slug)

        # bait probability
        bait = random.randint(1, 100)
        if self.value == "basic":
            if bait <= 35:
                mon_slug = random.choice(bas)
                level = random.randint(5, 15)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                return {"success": True}
            else:
                return {"success": False}
        elif self.value == "advanced":
            if bait <= 65:
                mon_slug = random.choice(adv)
                level = random.randint(15, 25)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                return {"success": True}
            else:
                return {"success": False}
        elif self.value == "pro":
            if bait <= 85:
                mon_slug = random.choice(pro)
                level = random.randint(25, 35)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                return {"success": True}
            else:
                return {"success": False}
        return {"success": False}
