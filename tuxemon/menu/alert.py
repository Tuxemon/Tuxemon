# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.constants.dialog_speed import resolve_character_delay
from tuxemon.prepare import CONFIG
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.animation import Task
    from tuxemon.sprite import Sprite, SpriteGroup


logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(
        self, sprites: SpriteGroup[Sprite], task_fn: Callable[..., Task]
    ) -> None:
        self.sprites = sprites
        self.task = task_fn
        self._dialog_lines: list[str] = []
        self._dialog_index: int = 0
        self._dialog_callback: Optional[Callable[[], None]] = None
        self.character_delay: float = 0.05

        self._alert_queue: deque[dict[str, Any]] = deque()
        self._is_busy: bool = False

    def find_textarea(self) -> TextArea:
        for sprite in self.sprites:
            if isinstance(sprite, TextArea):
                return sprite
        raise RuntimeError("No TextArea found for dialog.")

    def animate_text(
        self,
        text_area: TextArea,
        text: str,
        callback: Optional[Callable[[], None]] = None,
        character_delay: float = 0.05,
    ) -> None:
        text_area.text = text
        self.character_delay = character_delay

        if character_delay == 0.0:
            # Instantly dump all text — no animation
            try:
                for _ in text_area:
                    pass
            except Exception as e:
                logger.warning(f"Unexpected error while dumping text: {e}")
            if callback:
                callback()
        else:
            # Animate character-by-character
            self.start_text_animation(text_area, callback)

    def start_text_animation(
        self,
        text_area: TextArea,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        def next_character() -> None:
            try:
                next(text_area)
            except StopIteration:
                if callback:
                    callback()
            else:
                self.task(next_character, interval=self.character_delay)

        next_character()

    def alert(
        self,
        message: str,
        callback: Optional[Callable[[], None]] = None,
        dialog_speed: str = CONFIG.dialog_speed,
        split_lines: bool = False,
    ) -> None:
        self._alert_queue.append(
            {
                "message": message,
                "callback": callback,
                "dialog_speed": dialog_speed,
                "split_lines": split_lines,
            }
        )
        if not self._is_busy:
            self._process_next_alert()

    def _process_next_alert(self) -> None:
        if self._alert_queue:
            self._is_busy = True
            next_alert = self._alert_queue.popleft()

            message = next_alert["message"]
            callback = next_alert["callback"]
            dialog_speed = next_alert["dialog_speed"]
            split_lines = next_alert["split_lines"]

            character_delay = resolve_character_delay(dialog_speed)

            def alert_complete_callback() -> None:
                if callback:
                    callback()
                self._is_busy = False
                self._process_next_alert()

            if split_lines:
                self._dialog_lines = message.splitlines()
                self._dialog_index = 0
                self._dialog_callback = alert_complete_callback
                self.advance_dialog_line(character_delay)
            else:
                self.animate_text(
                    self.find_textarea(),
                    message,
                    alert_complete_callback,
                    character_delay,
                )
        else:
            self._is_busy = False

    def advance_dialog_line(self, character_delay: float = 0.05) -> None:
        if self._dialog_index < len(self._dialog_lines):
            line = self._dialog_lines[self._dialog_index]
            self._dialog_index += 1
            self.animate_text(
                self.find_textarea(),
                line,
                callback=self._dialog_callback,
                character_delay=character_delay,
            )
        else:
            self._dialog_lines = []
            self._dialog_index = 0
            if self._dialog_callback:
                self._dialog_callback()
                self._dialog_callback = None

    def dump_remaining_text(
        self, text_area: Optional[TextArea] = None
    ) -> None:
        """
        Instantly finishes rendering all remaining dialog text in the given TextArea.
        """
        area = text_area or self.find_textarea()
        try:
            for _ in area:
                pass
        except Exception as e:
            logger.warning(f"Error dumping remaining text: {e}")

    def is_dialog_complete(self, text_area: Optional[TextArea] = None) -> bool:
        """
        Checks if all text has finished rendering.
        """
        area = text_area or self.find_textarea()
        return not area.drawing_text
