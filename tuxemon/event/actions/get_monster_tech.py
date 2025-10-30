# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, final

from tuxemon.db import Comparison, Range
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.states.technique_menu import TechniqueMenuState
from tuxemon.tools import compare, get_valid_uuid, parse_flag

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class GetMonsterTechAction(EventAction):
    """
    Select a tech among the monster's moves. Supports filtering by slug, element,
    range, and numeric comparisons for power and accuracy.

    Accepted comparison operators: "less_than", "less_or_equal", "greater_than",
    "greater_or_equal", "equals", and "not_equals".

    Script usage:
        .. code-block::

            get_monster_tech <variable_name>,<monster_id>[,skip_eligibility_check]
                            [,filter_name][,value_name][,extra]

    Script parameters:
        variable_name: Name of the game variable where the technique ID will be
            stored.
        monster_id: Name of the game variable that contains the monster ID.
        skip_eligibility_check: Optional string flag to bypass level/evolution
            eligibility checks. Accepts "true", "1", or "yes" (case-insensitive).
        filter_name: Optional filter key—e.g., "slug", "element", "range",
            "power", or "accuracy".
        value_name: Value to apply against the filter (e.g., "water", "stage1",
            "greater_than").
        extra: Optional numeric value for comparison filters (e.g., "1.6").

    Examples:
        "get_monster_tech chosen_id,monster_ref"
        "get_monster_tech chosen_id,monster_ref,true"
        "get_monster_tech chosen_id,monster_ref,false,element,water"
        "get_monster_tech chosen_id,monster_ref,true,power,greater_than,2.0"
    """

    name = "get_monster_tech"
    variable_name: str
    monster_id: str
    skip_eligibility_check: Optional[str] = None
    filter_name: Optional[str] = None
    value_name: Optional[str] = None
    extra: Optional[str] = None

    def validate(self, technique: Optional[Technique]) -> bool:
        monster = self.monster

        filter_name = self.filter_name
        value_name = self.value_name

        if technique is None:
            return False

        skip_check = parse_flag(self.skip_eligibility_check)

        if not skip_check:
            if not monster.moves.can_forget(technique):
                logger.debug(
                    f"Technique '{technique.slug}' is not forgettable — skipping."
                )
                return False

        if filter_name is None and value_name is None:
            self.result = True
            return self.result
        if filter_name and value_name:
            # filter slug
            if filter_name == "slug" and technique.slug == value_name:
                self.result = True
                return self.result
            # filter element / type
            if filter_name == "element" and technique.has_type(value_name):
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

        player.game_variables.set(
            self.variable_name, technique.instance_id.hex
        )
        self.session.client.pop_state()

    def start(self, session: Session) -> None:
        self.session = session
        self.result = False
        self.choose = False
        player = session.player

        monster_id = get_valid_uuid(player.game_variables, self.monster_id)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.monster_id}'"
            )
            return  # Exit early if no valid UUID
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error(f"Monster not found")
            return
        monsters = [monster]

        for mon in monsters:
            self.monster: Monster = mon
            menu = session.client.push_state(
                TechniqueMenuState(
                    character=session.player,
                    techniques=mon.moves.get_moves(),
                )
            )
            menu.is_valid_entry = self.validate  # type: ignore[method-assign]
            menu.on_menu_selection = self.set_var  # type: ignore[assignment]

        # if without filters, no closing by clicking back
        if (
            self.filter_name is None
            and self.value_name is None
            and self.extra is None
        ):
            menu.escape_key_exits = False

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("TechniqueMenuState")
        except ValueError:
            player = session.player
            if self.result and not self.choose:
                # the player can choose, but returns
                player.game_variables.set(self.variable_name, "no_choice")
            if not self.result:
                # the player can't choose (eg no females in the party)
                player.game_variables.set(self.variable_name, "no_options")
            self.stop()
