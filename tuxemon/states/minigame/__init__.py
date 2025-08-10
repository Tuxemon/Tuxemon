# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from functools import partial

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.tools import fix_measure, open_dialog

lookup_cache: dict[str, MonsterModel] = {}


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = MonsterModel.lookup(mon, db)
        if results.txmn_id > 0:
            lookup_cache[mon] = results


DIFFICULTIES = ["easy", "normal", "hard"]


class DifficultySelectState(PygameMenuState):
    """
    A state that allows players to choose the difficulty level before entering the minigame.
    """

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE
        super().__init__(height=height, width=width)

        self._build_menu()
        self.reset_theme()

    def _build_menu(self) -> None:
        """
        Constructs the difficulty selection menu with a title label and difficulty buttons.
        """
        title = T.translate("choose_difficulty")
        self.menu.add.label(
            title=title,
            font_size=self.font_type.big,
            align=locals.ALIGN_CENTER,
            underline=True,
        )

        for level in DIFFICULTIES:
            self.menu.add.button(
                title=T.translate(f"level_{level}"),
                action=partial(self.start_minigame, level),
                button_id=f"diff_{level}",
                font_size=self.font_type.medium,
                selection_effect=HighlightSelection(),
                align=locals.ALIGN_CENTER,
            )

    def start_minigame(self, difficulty: str) -> None:
        """
        Transitions to the minigame with the selected difficulty.
        """
        self.client.replace_state("MinigameState", difficulty=difficulty)


class MinigameState(PygameMenuState):
    """Minigame where player guesses a monster using image or description."""

    def __init__(
        self, difficulty: str = "easy", streak: int = 0, score: int = 0
    ) -> None:
        if not lookup_cache:
            _lookup_monsters()

        width, height = prepare.SCREEN_SIZE
        self.difficulty = difficulty
        self.streak = streak
        self.score = score

        theme = self._setup_theme(prepare.BG_MINIGAME)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)
        self.add_menu_items(self.menu)
        self.reset_theme()

    def add_menu_items(self, menu: pygame_menu.Menu) -> None:
        name = T.translate("who_is_that")
        menu.add.label(
            title=name,
            label_id="question",
            font_size=self.font_type.big,
            align=locals.ALIGN_CENTER,
            underline=True,
        )

        data = list(lookup_cache.values())
        tuxemon = random.choice(data)
        self.tuxemon = tuxemon

        # Image Display Based on Difficulty
        image_path = f"gfx/sprites/battle/{tuxemon.slug}-front.png"
        if self.difficulty in ["easy", "normal"]:
            try:
                image = self._create_image(image_path)
                image.scale(prepare.SCALE, prepare.SCALE)
                menu.add.image(image_path=image.copy())
            except Exception:
                image = self._create_image(prepare.MISSING_IMAGE)
                image.scale(prepare.SCALE, prepare.SCALE)
                menu.add.image(image_path=image.copy())

        if self.difficulty == "hard":
            description = T.translate(f"{tuxemon.slug}_description")
            menu.add.label(
                title=description,
                font_size=self.font_type.small,
                label_id="description_label",
                align=locals.ALIGN_CENTER,
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
            align=locals.ALIGN_CENTER,
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
            frame.pack(label, align=locals.ALIGN_CENTER)

        # Score and Streak
        menu.add.label(
            title=f"{T.translate('score_label')}: {self.score}",
            label_id="score_label",
            font_size=self.font_type.medium,
            align=locals.ALIGN_CENTER,
        )
        menu.add.label(
            title=f"{T.translate('streak_label')}: {self.streak}",
            label_id="streak_label",
            font_size=self.font_type.medium,
            align=locals.ALIGN_CENTER,
        )

        if self.streak >= 10:
            menu.add.label(
                title=T.translate("streak_bonus"),
                font_size=self.font_type.medium,
                font_color=(255, 215, 0),
                label_id="streak_bonus_label",
                align=locals.ALIGN_CENTER,
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
            open_dialog(self.client, [T.translate("generic_wrong")])
