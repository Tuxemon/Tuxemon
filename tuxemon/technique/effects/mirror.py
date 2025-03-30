# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class MirrorEffect(TechEffect):
    """
    A mirror effect that switches the user and target sprites.

    The direction of the mirror effect can be specified using the `direction` parameter,
    which can be one of the following:
    - `both`: Switch both the user and target sprites.
    - `user_to_target`: Switch the user sprite to face the target.
    - `target_to_user`: Switch the target sprite to face the user.
    """

    name = "mirror"
    direction: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.combat_state
        assert combat

        user_sprite = combat._monster_sprite_map.get(user)
        target_sprite = combat._monster_sprite_map.get(target)

        assert user_sprite and target_sprite

        if self.direction == "both":
            front_user = user.get_sprite(
                "front", midbottom=target_sprite.rect.midbottom
            )
            back_target = target.get_sprite(
                "back", midbottom=user_sprite.rect.midbottom
            )
            combat.sprites.add(front_user)
            combat.sprites.add(back_target)
            combat._monster_sprite_map[user] = back_target
            combat._monster_sprite_map[target] = front_user
            combat.sprites.remove(user_sprite)
            combat.sprites.remove(target_sprite)

        elif self.direction == "user_to_target":
            side = (
                "front"
                if "left" == combat.get_side(user_sprite.rect)
                else "back"
            )
            front_user = user.get_sprite(
                side, midbottom=target_sprite.rect.midbottom
            )
            combat.sprites.add(front_user)
            combat._monster_sprite_map[target] = front_user
            combat.sprites.remove(target_sprite)

        elif self.direction == "target_to_user":
            side = (
                "back"
                if "left" == combat.get_side(user_sprite.rect)
                else "front"
            )
            back_target = target.get_sprite(
                side, midbottom=user_sprite.rect.midbottom
            )
            combat.sprites.add(back_target)
            combat._monster_sprite_map[user] = back_target
            combat.sprites.remove(user_sprite)

        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
