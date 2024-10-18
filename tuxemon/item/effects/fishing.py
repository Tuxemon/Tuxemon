# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import prepare
from tuxemon.db import EvolutionStage, MonsterModel, MonsterShape, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster

lookup_cache: dict[str, MonsterModel] = {}


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
    ) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_monsters()

        monster_lists = {
            "fishing_rod": _get_basic_monsters(),
            "neptune": _get_advanced_monsters(),
            "poseidon": _get_pro_monsters(),
        }

        if item.slug in monster_lists and random.random() <= self.bait:
            mon_slug = random.choice(monster_lists[item.slug])
            level = random.randint(self.lower_bound, self.upper_bound)
            self._trigger_fishing_encounter(mon_slug, level)
            return ItemEffectResult(
                name=item.name, success=True, num_shakes=0, extra=[]
            )
        return ItemEffectResult(
            name=item.name, success=False, num_shakes=0, extra=[]
        )

    def _trigger_fishing_encounter(self, mon_slug: str, level: int) -> None:
        """Trigger a fishing encounter"""
        client = self.session.client
        player = self.session.player
        environment = (
            "night_ocean"
            if player.game_variables["stage_of_day"] == "night"
            else "ocean"
        )
        blue = prepare.SEA_BLUE_COLOR
        rgb = ":".join(map(str, blue))
        client.event_engine.execute_action(
            "wild_encounter",
            [mon_slug, level, None, None, environment, rgb],
            True,
        )


def _get_basic_monsters() -> list[str]:
    """Return a list of basic monster slugs"""
    return [
        mon.slug
        for mon in lookup_cache.values()
        if mon.stage == EvolutionStage.basic
        and mon.shape in [MonsterShape.polliwog, MonsterShape.piscine]
    ]


def _get_advanced_monsters() -> list[str]:
    """Return a list of advanced monster slugs"""
    return [
        mon.slug
        for mon in lookup_cache.values()
        if mon.stage in [EvolutionStage.stage1, EvolutionStage.basic]
        and mon.shape in [MonsterShape.polliwog, MonsterShape.piscine]
    ]


def _get_pro_monsters() -> list[str]:
    """Return a list of pro monster slugs"""
    return [
        mon.slug
        for mon in lookup_cache.values()
        if mon.stage != EvolutionStage.basic
        and mon.shape
        in [
            MonsterShape.polliwog,
            MonsterShape.piscine,
            MonsterShape.leviathan,
        ]
    ]


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results
