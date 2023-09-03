# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import EvolutionStage, MonsterShape, db
from tuxemon.event.actions.wild_encounter import WildEncounterAction
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class FishingEffectResult(ItemEffectResult):
    pass


@dataclass
class FishingEffect(ItemEffect):
    """This effect triggers fishing."""

    name = "fishing"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> FishingEffectResult:
        # define random encounters
        fishing: bool = False
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
                        or results.shape == MonsterShape.piscine
                    ):
                        bas.append(results.slug)
                if (
                    results.stage == EvolutionStage.stage1
                    or results.stage == EvolutionStage.basic
                ):
                    if (
                        results.shape == MonsterShape.polliwog
                        or results.shape == MonsterShape.piscine
                    ):
                        adv.append(results.slug)
                if results.stage != EvolutionStage.basic:
                    if (
                        results.shape == MonsterShape.polliwog
                        or results.shape == MonsterShape.piscine
                        or results.shape == MonsterShape.leviathan
                    ):
                        pro.append(results.slug)

        # bait probability
        bait = random.randint(1, 100)
        if item.slug == "fishing_rod":
            if bait <= 35:
                mon_slug = random.choice(bas)
                level = random.randint(5, 15)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                fishing = True
        elif item.slug == "neptune":
            if bait <= 65:
                mon_slug = random.choice(adv)
                level = random.randint(15, 25)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                fishing = True
        elif item.slug == "poseidon":
            if bait <= 85:
                mon_slug = random.choice(pro)
                level = random.randint(25, 35)
                WildEncounterAction(
                    monster_slug=mon_slug, monster_level=level, env="ocean"
                ).start()
                fishing = True
        return {"success": fishing, "num_shakes": 0, "extra": None}
