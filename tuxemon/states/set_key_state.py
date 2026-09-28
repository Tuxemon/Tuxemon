# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.menu.transitions import PopInClamped
from tuxemon.platform.platform_pygame.events import KeyBindingRules

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class SetKeyState(PygameMenuState):
    """
    This state is responsible for setting the input keys.
    This only works for pygame events.
    """

    name: ClassVar[str] = "SetKeyState"

    def __init__(self, client: BaseClient, value: str, **kwargs: Any) -> None:
        self.value = value

        super().__init__(client=client, transition=PopInClamped(), **kwargs)

        theme = get_theme(self.client.context.scaling)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.menu.add.label(
            T.translate("options_new_input_key0").upper(),
            font_size=self.font_type.small,
        )
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        """
        Accepts a PlayerInput event and binds the first valid keycode.
        Assumes event.value is already normalized by InputConfig.
        """
        if not event.pressed:
            return None

        pressed_key = self.client.config.input.normalize_key(event.value)

        if pressed_key is None:
            return None  # ignore unmappable input

        if KeyBindingRules.is_valid_binding(pressed_key):
            self.client.remove_state_by_name("SetKeyState")
            self.client.config.update_control(self.value, pressed_key)

            keyboard = self.client.input_manager.core_devices.keyboard
            if keyboard is not None:
                keyboard.reload_mapping(
                    self.client.config.input.keyboard_button_map
                )

            return None

        return None
