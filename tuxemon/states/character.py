# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon import formula
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.entity.npc import NPC
from tuxemon.graphics import scale_surface
from tuxemon.locale.locale import T
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BG_PLAYER1, BG_PLAYER2
from tuxemon.platform.const.sizes import U_KM, U_MI
from tuxemon.tools import fix_measure, format_playtime
from tuxemon.tuxepedia.reporter import TuxepediaReporter

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class CharacterState(PygameMenuState):
    """
    This state is responsible for the character menu.

    By clicking right, it gives access to the Party Menu.

    Shows details of the character (e.g. monster captured, seen,
    battles, wallet, etc.).
    """

    name: ClassVar[str] = "CharacterState"

    def add_menu_items(
        self,
        menu: Menu,
    ) -> None:
        def fxw(r: float) -> int:
            return fix_measure(menu._width, r)

        def fxh(r: float) -> int:
            return fix_measure(menu._height, r)

        name = (
            T.translate(self.char.slug)
            if self.char.name == ""
            else self.char.name
        )

        # tuxepedia data
        filters = list(self.cache.values())
        reporter = TuxepediaReporter(self.char.tuxepedia.data)
        completeness = reporter.get_completeness_report(len(filters))
        percentage = round(completeness["registered_percent"] * 100, 1)
        seen = self.char.tuxepedia.get_seen_count()
        caught = self.char.tuxepedia.get_caught_count()

        if self.char.tuxepedia.data.entries:
            _msg_progress = {"value": str(percentage)}
            _msg_seen = {"param": str(seen + caught), "all": str(len(filters))}
            _msg_caught = {"param": str(caught), "all": str(len(filters))}
        else:
            _msg_progress = {"value": "-"}
            _msg_seen = {"param": "-", "all": "-"}
            _msg_caught = {"param": "-", "all": "-"}

        msg_progress = T.format("tuxepedia_progress", _msg_progress)
        msg_seen = T.format("tuxepedia_data_seen", _msg_seen)
        msg_caught = T.format("tuxepedia_data_caught", _msg_caught)

        play_time = format_playtime(self.char.session._total_playtime)
        msg_begin = f"{T.translate('player_total_playtime')}: {play_time}"

        if self.char.battle_handler.get_battles():
            summary = self.char.battle_handler.get_battle_outcome_summary()
            tot, won, lost, draw = (
                summary["total"],
                summary["won"],
                summary["lost"],
                summary["draw"],
            )

            _msg_battles = {
                "tot": str(tot),
                "won": str(won),
                "draw": str(draw),
                "lost": str(lost),
            }
            msg_battles = T.format("player_battles", _msg_battles)
        else:
            msg_battles = ""
        # steps
        steps = self.char.steps
        unit = self.client.config.unit_measure
        if unit == "metric":
            walked = formula.convert_km(steps)
            unit_walked = U_KM
        else:
            walked = formula.convert_mi(steps)
            unit_walked = U_MI
        _msg_walked = {"distance": str(walked), "unit": unit_walked}
        msg_walked = T.format("player_walked", _msg_walked)
        # name
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=name.upper(),
            label_id="name",
            font_size=self.font_type.big,
            align=ALIGN_LEFT,
            underline=True,
            float=True,
        )
        lab1.translate(fxw(0.45), fxh(0.15))
        # money
        money = CurrencyFormatter()
        amount = self.char.money_controller.money_manager.get_money()
        lab2: Any = menu.add.label(
            title=f"{T.translate('wallet')}: {money.format(amount)}",
            label_id="money",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fxw(0.45), fxh(0.25))
        # seen
        lab3: Any = menu.add.label(
            title=msg_seen,
            label_id="seen",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fxw(0.45), fxh(0.30))
        # caught
        lab4: Any = menu.add.label(
            title=msg_caught,
            label_id="caught",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fxw(0.45), fxh(0.35))
        # total playtime
        lab5: Any = menu.add.label(
            title=msg_begin,
            label_id="begin",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab5.translate(fxw(0.45), fxh(0.40))
        # walked
        if steps > 0.0:
            lab6: Any = menu.add.label(
                title=msg_walked,
                label_id="walked",
                font_size=self.font_type.smaller,
                align=ALIGN_LEFT,
                float=True,
            )
            lab6.translate(fxw(0.45), fxh(0.45))
        # battles
        lab7: Any = menu.add.label(
            title=msg_battles,
            label_id="battle",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab7.translate(fxw(0.45), fxh(0.50))
        # % tuxepedia
        lab8: Any = menu.add.label(
            title=msg_progress,
            label_id="progress",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab8.translate(fxw(0.45), fxh(0.10))
        # image
        surface = self.char.combat_sheet.front()
        scaled = scale_surface(surface, self.factor)
        new_image = self._create_image_from_surface(scaled)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(fxw(0.20), fxh(0.08))

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        **kwargs: Any,
    ) -> None:
        MonsterModel.load_cache(db)
        self.cache = MonsterModel.get_cache()

        width, height = client.context.resolution
        self.char = character

        bg = (
            BG_PLAYER2
            if self.char.monsters and self.char.is_player
            else BG_PLAYER1
        )

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(bg)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        if (
            event.button == buttons.RIGHT
            and event.pressed
            and self.char.monsters
        ):
            self.client.replace_state("PartyState", party=self.char.party)
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            self.client.pop_state()
        return None
