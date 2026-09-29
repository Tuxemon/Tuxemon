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
from tuxemon.session import Session
from tuxemon.technique.technique import Technique
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@dataclass
class Movesets:
    name: str
    techniques: list[dict[str, Any]]


class Loader:
    _config_moves: dict[str, Movesets] = {}

    @classmethod
    def get_config_moves(cls, filename: str) -> dict[str, Movesets]:
        if not cls._config_moves:
            yaml_path = paths.mods_folder / filename
            raw_data = load_yaml(yaml_path)
            movesets_data = raw_data.get("movesets", {})
            cls._config_moves = {
                name: Movesets(name=name, techniques=techs)
                for name, techs in movesets_data.items()
                if isinstance(techs, list)
            }
        return cls._config_moves


@final
@dataclass
class ReplaceTechsFromYamlAction(EventAction):
    """
    Replaces a monster's moveset using a predefined set from a YAML file.

    Script usage:
        .. code-block::

            replace_techs_from_yaml <variable>,<yaml_file>,<set_name>

    Script parameters:
        variable: Name of the variable where the monster UUID is stored.
        yaml_file: Path to the YAML file containing movesets.
        set_name: The key of the moveset to use within the YAML file.

    Examples:
        "replace_techs_from_yaml monster_id,movesets,starter_set"
    """

    name = "replace_techs_from_yaml"
    variable: str
    yaml_file: str
    set_name: str

    def start(self, session: Session) -> None:
        player = session.player

        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID
        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.error("Monster not found")
            self.stop()
            return

        movesets = Loader.get_config_moves(f"{self.yaml_file}.yaml")
        moveset = movesets.get(self.set_name)

        if not moveset:
            logger.error(
                f"Moveset '{self.set_name}' not found in '{self.yaml_file}'"
            )
            self.stop()
            return

        move_slugs = [
            item["slug"] for item in moveset.techniques if "slug" in item
        ]
        weights = [
            item.get("weight", 1)
            for item in moveset.techniques
            if "slug" in item
        ]

        if len(move_slugs) > monster.max_moves:
            logger.warning(
                f"Moveset '{self.set_name}' contains more moves than allowed "
                f"({len(move_slugs)} > {monster.max_moves}). Randomly selecting {monster.max_moves}."
            )
            moves_to_use = random.choices(
                move_slugs, weights=weights, k=monster.max_moves
            )
        else:
            moves_to_use = move_slugs

        new_moves = [Technique.create(tech_slug) for tech_slug in moves_to_use]
        monster.moves.replace_all_moves(new_moves)
        logger.info(
            f"Replaced all moves for {monster.name} using set '{self.set_name}' from {self.yaml_file}"
        )
