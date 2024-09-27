# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Comparison, ElementType, Range
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.states.techniques import TechniqueMenuState
from tuxemon.technique.technique import Technique
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class GetMonsterTechAction(EventAction):
    """
    Select a tech among the monster's moves.
    It allows filtering: slug, element, range.

    eg "get_monster_tech name_variable"

    For the definition: power and accuracy (all numeric values) is necessary
    to use a numeric comparison operator. Accepted values are "less_than",
    "less_or_equal", "greater_than", "greater_or_equal", "equals" and
    "not_equals".

    Script usage:
        .. code-block::

            get_monster_tech <variable_name>,<monster_id>[,filter_name][,value_name][,extra]

    Script parameters:
        variable_name: Variable where to store the technique id.
        monster_id: Variable where is stored the monster id.
        filter_name: the name of the first filter
        value_name: the actual value to filter
        extra: used to filter more

    eg. "get_monster_tech name_variable,monster_id"
    eg. "get_monster_tech name_variable,monster_id,element,water"
    eg, "get_monster_tech name_variable,monster_id,power,less_than,1.6"

    """

    name = "get_monster_tech"
    variable_name: str
    monster_id: Optional[str] = None
    filter_name: Optional[str] = None
    value_name: Optional[str] = None
    extra: Optional[str] = None

    def validate(self, technique: Optional[Technique]) -> bool:
        filter_name = self.filter_name
        value_name = self.value_name
        if filter_name is None and value_name is None:
            self.result = True
            return self.result
        if filter_name and value_name and technique:
            # filter slug
            if filter_name == "slug" and technique.slug == value_name:
                self.result = True
                return self.result
            # filter element / type
            if (
                filter_name == "element"
                and value_name in list(ElementType)
                and technique.has_type(ElementType(value_name))
            ):
                self.result = True
                return self.result
            # filter genders
            if (
                filter_name == "range"
                and value_name in list(Range)
                and technique.range == value_name
            ):
                self.result = True
                return self.result
            # filter numeric fields
            if self.extra is not None:
                field = 0.0
                if filter_name == "power":
                    field = technique.power
                if filter_name == "accuracy":
                    field = technique.accuracy
                extra = float(self.extra)
                if value_name in list(Comparison):
                    self.result = compare(value_name, field, extra)
                    return self.result
        return False

    def set_var(self, menu_item: MenuItem[Technique]) -> None:
        self.choose = True
        player = self.session.player
        technique = menu_item.game_object

        player.game_variables[self.variable_name] = str(
            technique.instance_id.hex
        )
        self.session.client.pop_state()

    def start(self) -> None:
        self.result = False
        self.choose = False
        player = self.session.player
        client = self.session.client

        if self.monster_id is None:
            monsters = client.event_data.get("check_max_tech", [])
            client.event_data.pop("check_max_tech")
        else:
            if self.monster_id not in player.game_variables:
                logger.error(f"Game variable {self.monster_id} not found")
                return
            monster_id = uuid.UUID(
                player.game_variables[self.monster_id],
            )
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error(f"Monster not found")
                return
            monsters = [monster]

        for mon in monsters:
            # pull up the monster menu so we know which one we are saving
            menu = self.session.client.push_state(
                TechniqueMenuState(monster=mon)
            )
            menu.is_valid_entry = self.validate  # type: ignore[assignment]
            menu.on_menu_selection = self.set_var  # type: ignore[assignment]

        # if without filters, no closing by clicking back
        if (
            self.filter_name is None
            and self.value_name is None
            and self.extra is None
        ):
            menu.escape_key_exits = False

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(TechniqueMenuState)
        except ValueError:
            player = self.session.player
            if self.result and not self.choose:
                # the player can choose, but returns
                player.game_variables[self.variable_name] = "no_choice"
            if not self.result:
                # the player can't choose (eg no females in the party)
                player.game_variables[self.variable_name] = "no_options"
            self.stop()
