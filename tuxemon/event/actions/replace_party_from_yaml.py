# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, final

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.platform.const.sizes import PARTY_LIMIT
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class Parties:
    name: str
    monsters: list[dict[str, Any]]


class Loader:
    _config_monsters: dict[str, Parties] = {}

    @classmethod
    def get_config_monsters(cls, filename: str) -> dict[str, Parties]:
        if not cls._config_monsters:
            yaml_path = paths.mods_folder / filename
            raw_data = load_yaml(yaml_path)
            parties_data = raw_data.get("parties", {})
            cls._config_monsters = {
                name: Parties(name=name, monsters=entries)
                for name, entries in parties_data.items()
                if isinstance(entries, list)
            }
        return cls._config_monsters


@final
@dataclass
class ReplacePartyFromYamlAction(EventAction):
    """
    Replaces a character's party with a predefined set of monsters from a YAML file.

    This action loads a named party configuration from a YAML file and assigns it
    to the specified character (either the player or an NPC). Each monster entry
    in the YAML can define attributes like slug, level, and weight for random selection.

    Script usage:
        .. code-block::

            replace_party_from_yaml <character>,<yaml_file>,<set_name>

    Script parameters:
        character: Either "player" or an NPC slug (e.g. "npc_maple").
        yaml_file: Name of the YAML file (without extension) located in the mods folder.
        set_name: The key of the party to use within the YAML file.

    Examples:
        "replace_party_from_yaml npc_maple,parties,starter_set"
    """

    name = "replace_party_from_yaml"
    character: str
    yaml_file: str
    set_name: str

    def start(self, session: Session) -> None:

        character = session.client.get_npc(self.character)
        if character is None:
            logger.error("'wild_encounter' not found")
            self.stop()
            return

        parties = Loader.get_config_monsters(f"{self.yaml_file}.yaml")
        party = parties.get(self.set_name)

        if not party:
            logger.error(
                f"Party '{self.set_name}' not found in '{self.yaml_file}'"
            )
            self.stop()
            return

        monster_defs = party.monsters
        weights = [entry.get("weight", 1) for entry in monster_defs]

        if len(monster_defs) > PARTY_LIMIT:
            selected = random.choices(
                monster_defs, weights=weights, k=PARTY_LIMIT
            )
        else:
            selected = monster_defs

        new_monsters = []
        for entry in selected:
            slug = entry.get("slug")
            level = entry.get("level", 1)
            if not slug:
                logger.warning(f"Missing slug in party entry: {entry}")
                continue

            monster = Monster.spawn_base(slug, level)
            character.tuxepedia.register_caught(monster.slug)

            if "experience_modifier" in entry:
                monster.set_experience_modifier(
                    float(entry["experience_modifier"])
                )
            if "money_modifier" in entry:
                monster.money_modifier = float(entry["money_modifier"])

            new_monsters.append(monster)

        if not new_monsters:
            logger.error(
                f"No valid monsters built for set '{self.set_name}', party unchanged."
            )
            self.stop()
            return

        character.party.replace_party(new_monsters, False)
        logger.info(
            f"Replaced all monsters for {character.name} using set '{self.set_name}' from {self.yaml_file}"
        )
