# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random

from tuxemon.database.runtime import db
from tuxemon.db import DialogueContent, DialogueProfile, NpcModel


class DialogueProfileManager:
    """
    Manages the loading, caching, and retrieval of NPC dialogue.
    """

    def __init__(self) -> None:
        self.dialogue_cache: dict[str, DialogueProfile] = {}

    def get_npc_dialogue_content(
        self, npc_slug: str, location: str | None = None
    ) -> DialogueContent:
        """
        Retrieves the effective DialogueContent object for an NPC at a given location.
        This is the internal method for getting the full content model.
        """
        if npc_slug not in self.dialogue_cache:
            npc_details: NpcModel = NpcModel.lookup(npc_slug, db)
            self.dialogue_cache[npc_slug] = npc_details.speech.profile

        dialogue_model = self.dialogue_cache[npc_slug]

        if location:
            return dialogue_model.get_dialogue_for_location(location)

        return dialogue_model.default

    def get_dialogue_line(
        self, content: DialogueContent, field_name: str
    ) -> str | None:
        """
        Extracts and returns a single random dialogue string from a field.
        Handles both single strings and lists of strings.
        """
        dialogue_field: str | list[str] | None = getattr(
            content, field_name, None
        )

        if not dialogue_field:
            return None

        if isinstance(dialogue_field, list):
            return random.choice(dialogue_field)

        return dialogue_field

    def get_pre_battle_dialogue(
        self, npc_slug: str, location: str | None = None
    ) -> str | None:
        """Convenience method to get the pre-battle dialogue for an NPC."""
        content = self.get_npc_dialogue_content(npc_slug, location)
        return self.get_dialogue_line(content, "pre_battle")

    def get_post_battle_win_dialogue(
        self, npc_slug: str, location: str | None = None
    ) -> str | None:
        """Convenience method to get the post-battle dialogue for an NPC."""
        content = self.get_npc_dialogue_content(npc_slug, location)
        return self.get_dialogue_line(content, "post_battle_win")

    def get_post_battle_lose_dialogue(
        self, npc_slug: str, location: str | None = None
    ) -> str | None:
        """Convenience method to get the post-battle dialogue for an NPC."""
        content = self.get_npc_dialogue_content(npc_slug, location)
        return self.get_dialogue_line(content, "post_battle_lose")

    def get_post_battle_draw_dialogue(
        self, npc_slug: str, location: str | None = None
    ) -> str | None:
        """Convenience method to get the post-battle dialogue for an NPC."""
        content = self.get_npc_dialogue_content(npc_slug, location)
        return self.get_dialogue_line(content, "post_battle_draw")

    def get_greeting_dialogue(
        self, npc_slug: str, location: str | None = None
    ) -> str | None:
        """Convenience method to get the greeting dialogue for an NPC."""
        content = self.get_npc_dialogue_content(npc_slug, location)
        return self.get_dialogue_line(content, "greeting")
