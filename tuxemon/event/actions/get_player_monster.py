# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import Comparison, EvolutionStage, GenderType, StatType
from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@final
@dataclass
class GetPlayerMonsterAction(EventAction):
    """
    Select a monster in the player party and store its id in a variable.
    It allows filtering: slug, gender, evolution_stage, element, shape,
    taste_warm, taste_cold, level, weight, height, max_hp, current_hp,
    armour, dodge, melee, ranged and speed.

    eg "get_player_monster name_variable,shape,serpent"
    eg "get_player_monster name_variable,shape,serpent"

    For the definition: level, weight, height, max_hp, current_hp, armour, dodge,
    melee, ranged and speed (all numeric values) is necessary to use a numeric
    comparison operator. Accepted values are "less_than", "less_or_equal",
    "greater_than", "greater_or_equal", "equals" and "not_equals".

    eg "get_player_monster name_variable,speed,more_than,50"
    eg "get_player_monster name_variable,level,less_than,15"

    Note:
    let's say a player doesn't has no options, then the variable
    will result as: name_variable:no_option
    let's say a player has options, but clicks return, then the
    variable will result as: name_variable:no_choice

    Script usage:
        .. code-block::

            get_player_monster <variable_name>,<filter_name>,<value_name>[,extra]

    Script parameters:
        variable_name: Name of the variable where to store the monster id.
        filter
        filter_name: the name of the first filter
        value_name: the actual value to filter
        extra: used to filter more
    """

    name = "get_player_monster"
    variable_name: str
    filter_name: str | None = None
    value_name: str | None = None
    extra: str | None = None

    def validate(self, target: Monster | None) -> bool:
        filter_name = self.filter_name
        value_name = self.value_name

        if filter_name is None and value_name is None:
            self.result = True
            return self.result

        if target:
            # filter slug
            if filter_name == "slug" and target.slug == value_name:
                self.result = True
                return self.result
            # filter genders
            if (
                filter_name == "gender"
                and value_name in list(GenderType)
                and target.gender == value_name
            ):
                self.result = True
                return self.result
            # filter evolution stages
            if (
                filter_name == "evolution_stage"
                and value_name in list(EvolutionStage)
                and target.stage == value_name
            ):
                self.result = True
                return self.result
            # filter element / type
            if (
                filter_name == "element"
                and value_name
                and target.has_type(value_name)
            ):
                self.result = True
                return self.result
            # filter shape
            if filter_name == "shape" and target.shape.slug == value_name:
                self.result = True
                return self.result
            # filter taste warm
            if filter_name == "taste_warm" and target.taste_warm == value_name:
                self.result = True
                return self.result
            # filter taste cold
            if filter_name == "taste_cold" and target.taste_cold == value_name:
                self.result = True
                return self.result

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
                elif filter_name in list(StatType):
                    field = target.return_stat(filter_name)
                extra = int(self.extra)
                if value_name in list(Comparison):
                    self.result = compare(value_name, field, extra)
                    return self.result

        return False

    def set_var(self, menu_item: MenuItem[Monster | None]) -> None:
        self.choose = True
        monster = menu_item.game_object
        if monster is None:
            return

        player = self.session.player
        player.game_variables.set(self.variable_name, monster.instance_id.hex)
        self.session.client.pop_state()

    def start(self, session: Session) -> None:
        self.session = session
        self.result = False
        self.choose = False
        # pull up the monster menu so we know which one we are saving
        menu = session.client.push_state(
            MonsterMenuState(
                session.client,
                session.player.monsters,
                on_selection=self.set_var,
                is_valid_entry=self.validate,
            )
        )
        # if without filters, no closing by clicking back
        if (
            self.filter_name is None
            and self.value_name is None
            and self.extra is None
        ):
            menu.escape_key_exits = False

    def update(self, session: Session, dt: float) -> None:
        if "MonsterMenuState" not in session.client.active_state_names:
            player = session.player
            if self.result and not self.choose:
                player.game_variables.set(self.variable_name, "no_choice")
            if not self.result:
                player.game_variables.set(self.variable_name, "no_options")
            self.stop()
