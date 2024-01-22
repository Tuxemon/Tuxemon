# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import prepare
from tuxemon.db import EvolutionStage, MonsterShape, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class FishingEffectResult(ItemEffectResult):
    pass


@dataclass
class FishingEffect(ItemEffect):
    """
    This effect triggers fishing.

    Parameters:
        bait: probability of fishing something
        lower_bound: min level of the fished monster
        upper_bound: max level of the fished monster

    """

    name = "fishing"
    bait: float
    lower_bound: int
    upper_bound: int

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> FishingEffectResult:
        # define random encounters
        mon_slug: str = ""
        level: int = 0
        fishing: bool = False
        bas: list[str] = []
        adv: list[str] = []
        pro: list[str] = []
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
        bait = random.random()
        if item.slug == "fishing_rod" and bait <= self.bait:
            mon_slug = random.choice(bas)
            level = random.randint(self.lower_bound, self.upper_bound)
            fishing = True
        elif item.slug == "neptune" and bait <= self.bait:
            mon_slug = random.choice(adv)
            level = random.randint(self.lower_bound, self.upper_bound)
            fishing = True
        elif item.slug == "poseidon" and bait <= self.bait:
            mon_slug = random.choice(pro)
            level = random.randint(self.lower_bound, self.upper_bound)
            fishing = True

        client = self.session.client
        player = self.session.player
        environment = (
            "night_ocean"
            if player.game_variables["stage_of_day"] == "night"
            else "ocean"
        )
        blue = prepare.SEA_BLUE_COLOR
        rgb = ":".join(map(str, blue))
        if fishing:
            client.event_engine.execute_action(
                "wild_encounter",
                [mon_slug, level, None, None, environment, rgb],
                True,
            )
        return {"success": fishing, "num_shakes": 0, "extra": None}
