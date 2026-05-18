# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE_CONTACTS
from tuxemon.platform.const.sizes import UNKNOWN_MAP_SLUG
from tuxemon.relationship import RelationshipConstants
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import MenuOptions, create_choice_options

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC

logger = logging.getLogger(__name__)


class Loader:
    _phone_calls_data: dict[str, Any] | None = None

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
            if self.current_map != required_map_slug:
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

        open_dialog(self.client, dialogue_text, dialog_speed="max")

    def choice(self, slug: str) -> None:
        """Opens the choice dialog to confirm the call."""
        self._current_call_slug = slug
        label = f"{T.translate('action_call')} {T.translate(slug).upper()}"
        actions = {slug: self._start_call}
        options = create_choice_options(actions)
        for opt in options:
            opt.display_text = label
        open_choice_dialog(
            self.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
        )

    def add_menu_items(
        self,
        menu: Menu,
    ) -> None:

        T_RELATIONSHIP = T.translate("relation_relationship")
        T_STRENGTH = T.translate("relation_strength")
        MAX_STRENGTH = RelationshipConstants.STRENGTH[1]

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

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character

        if self.char.current_map:
            self.current_map = self.char.current_map.split(".")[0]
        else:
            self.current_map = UNKNOWN_MAP_SLUG

        for relation in self.char.relationships.connections.values():
            relation.apply_decay(self.char.steps)

        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE_CONTACTS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
