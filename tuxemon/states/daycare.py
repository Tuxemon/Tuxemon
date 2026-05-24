# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.states.monster_menu import MonsterMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


class DaycareState(PygameMenuState):
    """
    Menu showing the status of the daycare:
    - Parents stored
    - Training EXP gained (combined)
    - Cost accumulated (combined)
    - EXP/cost per step (per monster + combined)
    - Breeding progress
    - newborn readiness
    - Buttons for Add / Withdraw / Collect newborn
    """

    name: ClassVar[str] = "DaycareState"

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.character = character
        self.daycare = character.daycare

        width, height = client.context.resolution
        width = int(0.8 * width)
        height = int(0.8 * height)

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.initialize_items(self.menu)
        self.reset_theme()

    def add_parent(self) -> None:
        menu = self.client.push_state(
            MonsterMenuState(
                client=self.client,
                monsters=self.character.party.monsters,
                on_selection=self._add_parent_callback,
            )
        )
        menu.escape_key_exits = False

    def _add_parent_callback(self, item: MenuItem[Monster | None]) -> None:
        monster = item.game_object if item else None

        if monster:
            self.daycare.add_parent(monster)

        self.client.pop_state()
        self.client.replace_state("DaycareState", character=self.character)

    def withdraw_all(self) -> None:
        if self.daycare.ready():
            newborn = self.daycare.produce_newborn()
            self.character.party.add_monster(newborn)
        self.daycare.withdraw_parents()
        self.client.pop_state()

    def collect_newborn(self) -> None:
        newborn = self.daycare.produce_newborn()
        self.character.party.add_monster(newborn)
        self.client.pop_state()

    def initialize_items(self, menu: Menu) -> None:
        dc = self.daycare
        parents = dc.parents

        # Summary
        menu.add.label(
            T.translate("menu_daycare_summary"),
            selectable=True,
            font_size=self.font_type.small,
        )
        menu.add.vertical_margin(10)

        # Parent count
        parent_count = len(parents)
        max_count = dc.MAX_PARENTS

        menu.add.label(
            f"{T.translate('menu_daycare_parents')} ({parent_count}/{max_count})",
            selectable=True,
            font_size=self.font_type.small,
        )

        if not parents:
            menu.add.label(
                T.translate("menu_daycare_empty"),
                font_size=self.font_type.smaller,
            )
        else:
            for m in parents:
                menu.add.label(
                    f"• {m.name} (Lv {m.level}, {m.gender_symbol})",
                    font_size=self.font_type.smaller,
                )

        menu.add.vertical_margin(10)

        # Mode
        if len(parents) == 1:
            mode = T.translate("menu_daycare_mode_training")
        elif len(parents) == 2:
            if dc._gender_pair_ok(parents[0], parents[1]):
                mode = T.translate("menu_daycare_mode_breeding")
            else:
                mode = T.translate("menu_daycare_mode_incompatible")
        else:
            mode = T.translate("menu_daycare_mode_empty")

        menu.add.label(
            f"{T.translate('menu_daycare_mode')}: {mode}",
            font_size=self.font_type.smaller,
        )

        menu.add.vertical_margin(10)

        # Training section
        menu.add.label(
            T.translate("menu_daycare_training"),
            selectable=True,
            font_size=self.font_type.small,
        )

        exp_total = dc.last_training_exp
        cost_total = dc.last_training_cost

        exp_rate = dc.training_exp_rate
        cost_rate = dc.training_cost_rate

        # Determine training count
        if len(parents) == 1:
            training_count = 1
        elif len(parents) == 2 and not dc._gender_pair_ok(
            parents[0], parents[1]
        ):
            training_count = 2
        else:
            training_count = 0

        effective_exp_rate = exp_rate * training_count
        effective_cost_rate = cost_rate * training_count

        # Totals
        menu.add.label(
            f"{T.translate('menu_daycare_exp_total')}: {exp_total}",
            font_size=self.font_type.smaller,
        )
        menu.add.label(
            f"{T.translate('menu_daycare_cost_total')}: {cost_total}",
            font_size=self.font_type.smaller,
        )

        # Per-step
        menu.add.label(
            f"{T.translate('menu_daycare_exp_per_step')}: {exp_rate} × {training_count}",
            font_size=self.font_type.smaller,
        )
        menu.add.label(
            f"{T.translate('menu_daycare_cost_per_step')}: {cost_rate} × {training_count}",
            font_size=self.font_type.smaller,
        )

        # Combined per-step
        menu.add.label(
            f"{T.translate('menu_daycare_exp_per_step_total')}: {effective_exp_rate}",
            font_size=self.font_type.smaller,
        )
        menu.add.label(
            f"{T.translate('menu_daycare_cost_per_step_total')}: {effective_cost_rate}",
            font_size=self.font_type.smaller,
        )

        # Training status
        if training_count == 1:
            menu.add.label(
                T.translate("menu_daycare_training_active_single"),
                font_size=self.font_type.smaller,
            )
        elif training_count == 2:
            menu.add.label(
                T.translate("menu_daycare_training_active_double"),
                font_size=self.font_type.smaller,
            )
        else:
            menu.add.label(
                T.translate("menu_daycare_training_inactive"),
                font_size=self.font_type.smaller,
            )

        menu.add.vertical_margin(10)

        # Breeding section
        menu.add.label(
            T.translate("menu_daycare_breeding"),
            selectable=True,
            font_size=self.font_type.small,
        )

        if len(parents) == 2 and dc._gender_pair_ok(parents[0], parents[1]):
            halfway = dc.required_steps // 2
            progress = dc.progress_steps

            menu.add.label(
                f"{T.translate('menu_daycare_progress')}: {progress:.0f}/{dc.required_steps}",
                font_size=self.font_type.smaller,
            )

            if progress >= dc.required_steps:
                menu.add.label(
                    T.translate("menu_daycare_ready"),
                    font_size=self.font_type.smaller,
                )
            elif progress >= halfway:
                menu.add.label(
                    T.translate("menu_daycare_halfway"),
                    font_size=self.font_type.smaller,
                )
            else:
                menu.add.label(
                    T.translate("menu_daycare_not_ready"),
                    font_size=self.font_type.smaller,
                )
        else:
            menu.add.label(
                T.translate("menu_daycare_no_breeding"),
                font_size=self.font_type.smaller,
            )

        menu.add.vertical_margin(20)

        # Add parent
        if parent_count < max_count:
            menu.add.button(
                T.translate("menu_daycare_add"),
                self.add_parent,
                font_size=self.font_type.small,
            )

        # Collect newborn
        if dc.ready():
            menu.add.button(
                T.translate("menu_daycare_collect"),
                self.collect_newborn,
                font_size=self.font_type.small,
            )

        # Withdraw
        if parent_count > 0:
            menu.add.button(
                T.translate("menu_daycare_withdraw"),
                self.withdraw_all,
                font_size=self.font_type.small,
            )

        menu.add.vertical_margin(20)

        menu.add.label(
            T.translate("menu_daycare_thanks"),
            selectable=True,
            font_size=self.font_type.small,
        )
