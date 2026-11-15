# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.entity.npc import NPC
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_MISSIONS
from tuxemon.platform.const.sizes import UNKNOWN_MAP_SLUG

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


@dataclass
class EmailData:
    id: str
    sender: str
    subject: str
    body: str
    date: Sequence[int]
    pc_tags: list[str]
    maps: list[str] | None = None


class EmailManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.emails: list[EmailData] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return

        data = load_yaml(self.path) or {}

        for entry in data.get("emails", []):
            self.emails.append(EmailData(**entry))

    def get_all(self) -> Sequence[EmailData]:
        return self.emails


class EmailState(PygameMenuState):
    """
    Displays a list of emails loaded from YAML and allows the player
    to read them in a simple menu interface.
    """

    name: ClassVar[str] = "EmailState"

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        tag_list: list[str],
        **kwargs: Any,
    ) -> None:
        self.char = character
        self.session = character.session
        self.tag_list = tag_list

        yaml_path = paths.mods_folder / "email.yaml"
        self.email_manager = EmailManager(yaml_path)

        if self.char.current_map:
            self.current_map = self.char.current_map.split(".")[0]
        else:
            self.current_map = UNKNOWN_MAP_SLUG

        width, height = client.context.resolution
        width = int(width * 0.8)
        height = int(height * 0.8)

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:
        menu.add.label(
            T.translate("menu_email"),
            selectable=True,
            font_size=self.font_type.medium,
        )
        menu.add.vertical_margin(10)

        emails = [
            e
            for e in self.email_manager.get_all()
            if any(tag in e.pc_tags for tag in self.tag_list)
            and (e.maps is None or self.current_map in e.maps)
        ]

        if not emails:
            menu.add.label(
                T.translate("menu_email_none"),
                font_size=self.font_type.small,
            )
            return

        # Sort by date (month, day)
        emails = sorted(emails, key=lambda e: tuple(e.date))

        for email in emails:
            menu.add.button(
                T.translate(email.subject),
                lambda e=email: self.open_email(e),
                font_size=self.font_type.small,
            )
            menu.add.vertical_margin(5)

    def open_email(self, email: EmailData) -> None:
        """Open a dedicated state to read a single email."""
        self.client.push_state("EmailReadState", email=email)


class EmailReadState(PygameMenuState):
    """
    Displays a single email in a clean, focused view.
    """

    name: ClassVar[str] = "EmailReadState"

    def __init__(
        self, client: BaseClient, email: EmailData, **kwargs: Any
    ) -> None:
        self.email = email

        width, height = client.context.resolution
        width = int(width * 0.7)
        height = int(height * 0.7)

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:
        menu.add.label(
            T.translate(self.email.subject),
            font_size=self.font_type.big,
            selectable=True,
        )
        menu.add.vertical_margin(10)

        menu.add.label(
            f"{T.translate('menu_email_from')}: {T.translate(self.email.sender)}",
            font_size=self.font_type.medium,
        )
        menu.add.vertical_margin(10)

        menu.add.label(
            T.translate(self.email.body),
            font_size=self.font_type.small,
            wordwrap=True,
        )

        menu.add.vertical_margin(20)
        menu.add.button(T.translate("menu_back"), self.client.pop_state)
