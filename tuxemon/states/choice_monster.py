# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.animation import Animation, ScheduleType
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.session import local_session
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


@dataclass
class MenuMonsterConfig:
    max_elements: int = 15
    max_height_percentage: float = 0.8
    animation_duration: float = 0.2
    animation_start_size: float = 0.0
    animation_end_size: float = 1.0
    number_widgets: int = 4
    number_columns: int = 5
    scale_sprite: float = 0.4
    vertical_fill: int = 20


class ChoiceMonster(PygameMenuState):
    """
    Game state with a graphic box and monsters (images) + labels.
    """

    name: ClassVar[str] = "ChoiceMonster"

    def __init__(
        self,
        client: BaseClient,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: MenuMonsterConfig | None = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuMonsterConfig()

        rows = (
            math.ceil(len(menu.options) / self.config.number_columns)
            * self.config.number_widgets
        )
        super().__init__(
            client=client,
            columns=self.config.number_columns,
            rows=rows,
            **kwargs,
        )

        theme = get_theme(self.client.context.scaling).copy()

        if len(menu.options) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        self._menu_config["theme"] = theme

        for option in menu.get_menu():
            self.add_monster_menu_item(
                option.display_text, option.key, option.action
            )

        self.animation_size = self.config.animation_start_size
        self.escape_key_exits = escape_key_exits

    def add_monster_menu_item(
        self,
        name: str,
        slug: str,
        pick_callback: Callable[[], None],
    ) -> None:
        monster = MonsterModel.lookup(slug, db)
        loader = SpriteLoader()
        sprites = monster.sprites
        assert sprites
        handler = MonsterSpriteHandler(
            slug=monster.slug,
            sheet_path=loader.resolve_path(sprites.sheet),
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
        )
        if handler is None:
            return
        sprite = handler.get_sprite(
            "front", scale=self.factor * self.config.scale_sprite
        )
        image = self._create_image_from_surface(sprite.image)
        self.menu.add.image(image, align=ALIGN_CENTER)

        self.menu.add.button(
            T.translate(name),
            lambda: self.open_journal(monster),
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )

        self.menu.add.button(
            T.translate("monster_menu_pick"),
            pick_callback,
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )

        self.menu.add.vertical_fill(self.config.vertical_fill)

    def open_journal(self, monster: MonsterModel) -> None:
        action = self.client.event_engine
        action.execute_action(
            "set_tuxepedia", ["player", monster.slug, "caught"], True
        )
        self.client.push_state(
            "JournalInfoState",
            character=local_session.player,
            monster=monster,
            source=self.name,
        )
        action.execute_action("clear_tuxepedia", [monster.slug], True)

    def update_animation_size(self) -> None:
        width, height = self.client.context.resolution
        widgets_size = self.menu.get_size(widget=True)

        _width = widgets_size[0]
        _height = widgets_size[1]

        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * self.config.max_height_percentage)

        self.menu.resize(
            max(1, int(_width * self.animation_size)),
            max(1, int(_height * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """Animate the menu popping in."""
        ani = self.animate(
            self,
            animation_size=self.config.animation_end_size,
            duration=self.config.animation_duration,
        )
        ani.schedule(self.update_animation_size, ScheduleType.ON_UPDATE)

        return ani
