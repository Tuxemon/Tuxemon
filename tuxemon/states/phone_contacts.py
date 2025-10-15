# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import pygame_menu
import yaml
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.relationship import RELATIONSHIP_STRENGTH
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open() as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


class Loader:
    _phone_calls_data: Optional[dict[str, Any]] = None

    @classmethod
    def get_phone_calls_data(cls, filename: str) -> dict[str, Any]:
        yaml_path = paths.mods_folder / filename
        if not cls._phone_calls_data:
            raw_data = load_yaml(yaml_path)
            if not isinstance(raw_data, dict):
                raise ValueError("Invalid YAML data for phone calls")
            cls._phone_calls_data = raw_data
        return cls._phone_calls_data


PHONE_CALLS_DATA = Loader.get_phone_calls_data("phone_calls.yaml")


class NuPhoneContacts(PygameMenuState):
    name: ClassVar[str] = "NuPhoneContacts"

    _current_call_slug: str = ""

    def _check_conditions(self, conditions: dict[str, Any]) -> bool:
        """
        Check if the required conditions (location and variables) are met.
        """
        required_map_slug = conditions.get("map_slug")
        if required_map_slug:
            current_map_slug = self.client.get_map_name().split(".")[0]
            if current_map_slug != required_map_slug:
                return False

        required_vars = conditions.get("variables")
        if required_vars:
            game_vars = self.char.game_variables
            for var_name, expected_value in required_vars.items():
                if game_vars.get(var_name) != expected_value:
                    return False

        return True

    def _start_call(self) -> None:
        """Handles the actual phone call logic based on dynamic data."""
        slug = self._current_call_slug
        self.client.remove_state_by_name("ChoiceState")

        npc_calls = PHONE_CALLS_DATA.get(slug, {})

        dialogue_msgids: list[str] = ["phone_no_answer"]

        conditional_calls = npc_calls.get("conditional_calls", [])
        for call in conditional_calls:
            conditions = call.get("conditions", {})
            if self._check_conditions(conditions):
                dialogue_msgids = call.get("dialogue", ["phone_no_answer"])
                break
        else:
            dialogue_msgids = npc_calls.get(
                "default", {"dialogue": ["phone_no_answer"]}
            ).get("dialogue")

        dialogue_text = [T.translate(msgid) for msgid in dialogue_msgids]

        open_dialog(
            self.client,
            dialogue_text,
        )

    def choice(self, slug: str) -> None:
        """Opens the choice dialog to confirm the call."""
        self._current_call_slug = slug
        label = f"{T.translate('action_call')} {T.translate(slug).upper()}"

        option = ChoiceOption(
            key=slug, display_text=label, action=self._start_call
        )

        open_choice_dialog(
            self.client,
            menu=MenuOptions([option]),
            escape_key_exits=True,
        )

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:

        T_RELATIONSHIP = T.translate("relation_relationship")
        T_STRENGTH = T.translate("relation_strength")
        MAX_STRENGTH = RELATIONSHIP_STRENGTH[1]

        connections = self.char.relationships.get_all_connections()
        for slug, contact in connections.items():

            menu.add.button(
                title=T.translate(slug),
                action=partial(self.choice, slug),
                font_size=self.font_type.small,
                selection_effect=HighlightSelection(),
            )

            # Relationship Type Label
            relation_type = T.translate(
                f"relation_{contact.relationship_type}"
            )
            menu.add.label(
                title=f"{T_RELATIONSHIP}: {relation_type}",
                font_size=self.font_type.small,
                padding=(5, 0, 5, 0),
            )

            # Relationship Strength Label
            menu.add.label(
                title=f"{T_STRENGTH}: {contact.strength}/{MAX_STRENGTH}",
                font_size=self.font_type.small,
                padding=(5, 0, 5, 0),
            )

            menu.add.vertical_margin(15)

        # menu
        menu.set_title(T.translate("app_contacts")).center_content()

    def __init__(self, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE_CONTACTS)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        theme.title = True

        self.char = character

        for relation in self.char.relationships.connections.values():
            relation.apply_decay(self.char)

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.reset_theme()
