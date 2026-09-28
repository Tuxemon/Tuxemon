# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.platform.const.graphics import BG_MINIGAME, MISSING_IMAGE
from tuxemon.tools import fix_measure, open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class MinigameState(PygameMenuState):
    """Minigame where player guesses a monster using image or description."""

    name: ClassVar[str] = "MinigameState"

    def __init__(
        self,
        client: BaseClient,
        difficulty: str = "easy",
        streak: int = 0,
        score: int = 0,
        **kwargs: Any,
    ) -> None:
        MonsterModel.load_cache(db)
        self.cache = MonsterModel.get_cache()

        width, height = client.context.resolution
        self.difficulty = difficulty
        self.streak = streak
        self.score = score

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MINIGAME)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()

    def add_menu_items(self, menu: Menu) -> None:
        name = T.translate("who_is_that")
        menu.add.label(
            title=name,
            label_id="question",
            font_size=self.font_type.big,
            align=ALIGN_CENTER,
            underline=True,
        )

        data = list(self.cache.values())
        tuxemon = random.choice(data)
        self.tuxemon = tuxemon

        # Image Display Based on Difficulty
        loader = SpriteLoader()
        sprites = tuxemon.sprites
        assert sprites
        handler = MonsterSpriteHandler(
            slug=tuxemon.slug,
            sheet_path=loader.resolve_path(sprites.sheet),
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
        )
        if handler is None:
            return
        sprite = handler.get_sprite("front", scale=self.factor)
        if self.difficulty in ["easy", "normal"]:
            try:
                image = self._create_image_from_surface(sprite.image)
                menu.add.image(image_path=image.copy())
            except Exception:
                image = self._create_image(MISSING_IMAGE)
                image.scale(self.factor, self.factor)
                menu.add.image(image_path=image.copy())

        if self.difficulty == "hard":
            description = T.translate(f"{tuxemon.slug}_description")
            menu.add.label(
                title=description,
                font_size=self.font_type.small,
                label_id="description_label",
                align=ALIGN_CENTER,
                max_char=-1,
                wordwrap=True,
            )

        # Monster choices
        num_choices = {"easy": 3, "normal": 5, "hard": 5}[self.difficulty]
        choice_pool = random.sample(data, num_choices)

        if tuxemon not in choice_pool:
            choice_pool[random.randint(0, num_choices - 1)] = tuxemon

        frame = menu.add.frame_h(
            width=fix_measure(menu._width, 0.95),
            height=fix_measure(menu._width, 0.05),
            frame_id="options",
            align=ALIGN_CENTER,
        )
        frame._relax = True

        for mon in choice_pool:
            label = menu.add.button(
                T.translate(mon.slug),
                partial(self.check_answer, mon),
                font_size=self.font_type.small,
                button_id=mon.slug,
                selection_effect=HighlightSelection(),
            )
            frame.pack(label, align=ALIGN_CENTER)

        # Score and Streak
        menu.add.label(
            title=f"{T.translate('score_label')}: {self.score}",
            label_id="score_label",
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )
        menu.add.label(
            title=f"{T.translate('streak_label')}: {self.streak}",
            label_id="streak_label",
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )

        if self.streak >= 10:
            menu.add.label(
                title=T.translate("streak_bonus"),
                font_size=self.font_type.medium,
                font_color=(255, 215, 0),
                label_id="streak_bonus_label",
                align=ALIGN_CENTER,
            )

    def check_answer(self, mon: MonsterModel) -> None:
        if mon.slug == self.tuxemon.slug:
            self.streak += 1
            self.score += {
                "easy": 1,
                "normal": 2,
                "hard": 3,
            }[self.difficulty]
            self.client.replace_state(
                "MinigameState",
                difficulty=self.difficulty,
                streak=self.streak,
                score=self.score,
            )

        else:
            self.streak = 0
            open_dialog(
                self.client, [T.translate("generic_wrong")], dialog_speed="max"
            )
