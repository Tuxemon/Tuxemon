# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.graphics import load_and_scale
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.ui.text import TextArea
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)


class DialogState(PopUpMenu[None]):
    """
    Game state with a graphic box and some text in it.

    Features:
    * Pressing the action button fast-forwards text.
    * When text is complete, shows the next message.
    * If no more messages, closes the dialog.
    * Optionally auto-closes after N seconds, either:
        - after the final line (default), or
        - per line (each line advances after N seconds).
    """

    name: ClassVar[str] = "DialogState"

    def __init__(
        self,
        client: BaseClient,
        rect: Rect,
        text: Sequence[str] = (),
        avatar: Sprite | None = None,
        box_style: dict[str, Any] | None = None,
        on_complete: Callable[[], None] | None = None,
        auto_close: bool = True,
        close_after: float | None = None,
        per_line_timeout: bool = False,
        advance_buttons: list[int] | None = None,
        dialog_speed: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, rect=rect.copy(), **kwargs)
        self.text_queue = list(text)
        self.avatar = avatar
        self.on_complete = on_complete
        self.auto_close = auto_close
        self.close_after = close_after
        self.advance_buttons = advance_buttons or [buttons.A]
        self.per_line_timeout = per_line_timeout
        self.dialog_speed = dialog_speed or self.client.config.dialog_speed

        self._elapsed_time: float = 0.0
        self._timer_active: bool = False

        default_box_style: dict[str, Any] = {
            "bg_color": self.background_color,
            "font_color": self.font_color,
            "font_shadow": self.font_shadow_color,
            "border": self.borders_filename,
            "line_spacing": 0,
            "h_alignment": HorizontalAlignment.LEFT,
            "v_alignment": VerticalAlignment.TOP,
        }

        final_box_style = default_box_style.copy()
        box_style = box_style or {}
        final_box_style.update(box_style)

        _border = load_and_scale(final_box_style["border"])
        self.window.set_border(_border)
        self.window.set_color(final_box_style["bg_color"])
        scaling = self.client.context.scaling
        line_spacing = scaling.scale_int(final_box_style["line_spacing"])

        internal_rect = self.calc_internal_rect().copy()

        self.dialog_box = TextArea(
            font=self.font,
            font_color=final_box_style["font_color"],
            rect=internal_rect,
            scaling=self.client.context.scaling,
            font_shadow=final_box_style["font_shadow"],
            h_alignment=final_box_style["h_alignment"],
            v_alignment=final_box_style["v_alignment"],
            line_spacing=line_spacing,
        )
        self.sprites.add(self.dialog_box)

    def on_open(self) -> None:
        """Start the dialog when the state is opened."""
        super().on_open()

        internal_rect = self.calc_internal_rect()
        logger.debug(f"DialogState.on_open: internal rect {internal_rect}")
        self.dialog_box.rect = internal_rect

        self.dialog_box.image = Surface(internal_rect.size, SRCALPHA)
        self.dialog_box.image = self.dialog_box._render_background()

        if self.avatar:
            avatar_rect = self.calc_final_rect()
            self.avatar.rect.bottomleft = avatar_rect.left, avatar_rect.top

        self.next_text()

        if not self.text_queue and not self.auto_close:
            self._timer_active = False

    def add_advance_button(self, button: int) -> None:
        """Add a button that can advance the dialog."""
        if button not in self.advance_buttons:
            self.advance_buttons.append(button)

    def remove_advance_button(self, button: int) -> None:
        """Remove a button from the dialog advance list."""
        if button in self.advance_buttons:
            self.advance_buttons.remove(button)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        """Handle player input to fast-forward or advance dialog lines."""
        if event.pressed and event.button in self.advance_buttons:
            if not self.dialog.is_dialog_complete(self.dialog_box):
                logger.debug("Fast-forwarding current dialog line")
                self.dialog.dump_remaining_text(self.dialog_box)
            else:
                if self.dialog.is_busy():
                    logger.debug(
                        "Ignoring rapid click during AlertManager transition."
                    )
                    return None
                if self.text_queue or self.auto_close:
                    self.next_text()
                    logger.debug("Dialog line complete, advancing to next")
        return None

    def update(self, dt: float) -> None:
        """Update dialog text, avatar, and auto-close timer each frame."""
        super().update(dt)

        if self.dialog_box.drawing_text:
            self.dialog.update(dt)

        if self.avatar:
            self.avatar.update(dt)

        # Handle auto-close countdown
        if self._timer_active and self.close_after is not None:
            self._elapsed_time += dt
            if self._elapsed_time >= self.close_after:
                if self.per_line_timeout and self.text_queue:
                    # Advance automatically to next line
                    logger.debug("Auto-advancing to next line after timeout")
                    self._timer_active = False
                    self.next_text()
                else:
                    # Close dialog after final line
                    logger.debug("Dialog auto-closing after timeout")
                    self.close_dialog()

    def next_text(self) -> str | None:
        """Advance to the next line of dialog or close when finished."""
        if self.dialog_box.drawing_text:
            return None

        if self.text_queue:
            text = self.text_queue.pop(0)

            if not text:
                return self.next_text()

            self.dialog.alert(
                message=text,
                text_area=self.dialog_box,
                dialog_speed=self.dialog_speed,
            )
            self._reset_timer()
            return text

        # No more text left
        self._reset_timer()

        if not self._timer_active and self.auto_close:
            self.close_dialog()

        return None

    def close_dialog(self) -> None:
        """Close the dialog immediately and trigger the completion callback."""
        self._timer_active = False
        self.client.event_bus.publish(
            "DIALOG_CLOSED",
            payload={
                "state": self.name,
                "auto_close": self.auto_close,
                "remaining_text": self.text_queue.copy(),
            },
        )
        if self.on_complete:
            try:
                self.on_complete()
            except Exception as e:
                logger.error(f"Error in on_complete callback: {e}")

        self.close()

    def _reset_timer(self) -> None:
        """Reset elapsed time and activate the timer if conditions are met."""
        self._elapsed_time = 0.0

        if self.close_after is not None:
            if self.per_line_timeout or not self.text_queue:
                self._timer_active = True
                return

        self._timer_active = False
