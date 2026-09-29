# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


class MonsterSpriteMap:
    def __init__(self) -> None:
        self.sprite_map: MutableMapping[NPC | Monster, Sprite] = {}

    def get_sprite(self, entity: NPC | Monster) -> Sprite | None:
        """Retrieves the sprite for the given entity, raising an error if not found."""
        if entity not in self.sprite_map:
            return None
        return self.sprite_map[entity]

    def add_sprite(self, entity: NPC | Monster, sprite: Sprite) -> None:
        """Associates a sprite with the given entity."""
        self.sprite_map[entity] = sprite

    def remove_sprite(self, entity: NPC | Monster) -> None:
        """Removes and cleans up the sprite associated with the given entity."""
        if entity in self.sprite_map:
            self.sprite_map[entity].kill()
            del self.sprite_map[entity]

    def update_sprite_position(
        self, entity: NPC | Monster, new_feet: tuple[int, int]
    ) -> None:
        """Updates the position of the given entity's sprite to match the new feet position."""
        if entity not in self.sprite_map:
            raise KeyError(
                f"Cannot update position: No sprite found for entity {entity.name}"
            )
        self.sprite_map[entity].rect.midbottom = new_feet
