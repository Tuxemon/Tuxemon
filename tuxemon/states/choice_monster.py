# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.baseimage import BaseImage
from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.widgets.core.widget import Widget
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.menu.transitions import PopInClamped
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.session import local_session
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


@dataclass
class MenuMonsterConfig:
    max_elements: int = 15
    max_height_percentage: float = 0.8
    animation_start_size: float = 0.0
    number_widgets: int = 4
    number_columns: int = 5
    # The animated 24x24 "menu" (face) sprite is shown at nominal pixel scale
    # (the game's scaling factor), not magnified beyond that.
    scale_sprite: float = 1.0
    vertical_fill: int = 20
    # Seconds each face animation frame is shown before alternating.
    frame_duration: float = 0.25


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
            transition=PopInClamped(
                max_height_percentage=self.config.max_height_percentage
            ),
            **kwargs,
        )

        theme = get_theme(self.client.context.scaling).copy()

        if len(menu.options) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        self._menu_config["theme"] = theme

        # Animated face sprites: each entry pairs an image widget with its two
        # pre-rendered frames, alternated on a shared timer in update().
        self._face_widgets: list[tuple[Widget, list[BaseImage]]] = []
        self._face_frame = 0
        self._face_timer = 0.0

        for option in menu.get_menu():
            self.add_monster_menu_item(
                option.display_text, option.key, option.action
            )

        self.animation_size = self.config.animation_start_size
        self.escape_key_exits = escape_key_exits

    def update(self, dt: float) -> None:
        super().update(dt)
        if not self._face_widgets:
            return
        self._face_timer += dt
        if self._face_timer < self.config.frame_duration:
            return
        self._face_timer = 0.0
        self._face_frame ^= 1
        for widget, frames in self._face_widgets:
            widget.set_image(frames[self._face_frame])
        # set_image alone only repaints on the next forced redraw (e.g. a
        # selection change), so force the menu to rebuild its cached surface
        # and the faces animate every frame.
        self.menu.force_surface_update()

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
        # Render the animated "menu" (face) sprite at native scale, rather than the
        # shrunk-down 64x64 front sprite. Both frames are pre-rendered once and
        # alternated by update().
        frames = handler.load_sprites(
            scale=self.factor * self.config.scale_sprite
        )
        face_frames = [
            self._create_image_from_surface(frames["menu01"]),
            self._create_image_from_surface(frames["menu02"]),
        ]
        widget = self.menu.add.image(face_frames[0], align=ALIGN_CENTER)
        self._face_widgets.append((widget, face_frames))

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
