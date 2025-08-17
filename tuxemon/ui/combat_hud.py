# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pygame.rect import Rect

from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


class Side(Enum):
    PLAYER = "player"
    OPPONENT = "opponent"


@dataclass
class MonsterUI:
    slot_index: int = 0
    layout_key: str = "home"
    hud_sprite: Optional[Sprite] = None
    status_icons: list[Sprite] = field(default_factory=list)
    feet_pos: tuple[int, int] = (0, 0)


class CombatLayoutManager:
    """
    Manages both battle positioning (sides and slot indices) and layout keys for HUD rendering.
    """

    def __init__(self, layouts: dict[NPC, dict[str, list[Rect]]]) -> None:
        self._layouts = layouts
        self._positions: dict[Monster, tuple[Side, int]] = {}
        self._layout_keys: dict[tuple[NPC, Monster], str] = {}
        self._hud_sprites: dict[Monster, Sprite] = {}
        self._monster_ui: dict[Monster, MonsterUI] = {}

    @property
    def layout(self) -> dict[NPC, dict[str, list[Rect]]]:
        return self._layouts

    @property
    def hud_map(self) -> dict[Monster, Sprite]:
        return self._hud_sprites

    def assign(
        self, nr_players: int, npc: NPC, monster: Monster, is_double: bool
    ) -> None:
        if monster in self._monster_ui:
            logger.debug(f"{monster.name} already assigned, skipping.")
            return
        side = Side.PLAYER if npc.is_player else Side.OPPONENT
        slot_index = self.get_open_slot(npc)

        if not is_double and nr_players == 2 and side == Side.PLAYER:
            slot_index = 1

        if not is_double and nr_players == 2 and side == Side.OPPONENT:
            slot_index = 0

        key = f"home{slot_index}" if is_double else "home"
        feet = self.get_feet_position(npc, monster)

        self._positions[monster] = (side, slot_index)
        self._layout_keys[(npc, monster)] = key
        self._monster_ui[monster] = MonsterUI(
            slot_index=slot_index,
            layout_key=key,
            feet_pos=feet,
        )

        logger.debug(
            f"[assign] {monster.name} → slot {slot_index}, key '{key}', side {side.name}"
        )

    def get_index(self, monster: Monster) -> int:
        return self._positions.get(monster, (None, 0))[1]

    def get_key(self, npc: NPC, monster: Monster) -> str:
        return self._layout_keys.get((npc, monster), "home")

    def get_open_slot(self, npc: NPC) -> int:
        used = set()
        for (n, _), key in self._layout_keys.items():
            if n != npc:
                continue
            if key == "home":
                used.add(0)
            elif key.startswith("home") and key[-1].isdigit():
                used.add(int(key[-1]))

        return 0 if 0 not in used else 1 if 1 not in used else 0

    def get_rect(self, npc: NPC, key: str) -> Rect:
        layout = self._layouts.get(npc)
        if not layout or key not in layout or not layout[key]:
            raise ValueError(f"Missing layout key '{key}' for NPC {npc.name}")
        return layout[key][0]

    def assign_hud(self, monster: Monster, sprite: Sprite) -> None:
        self._hud_sprites[monster] = sprite

    def get_hud(self, monster: Monster) -> Optional[Sprite]:
        return self._hud_sprites.get(monster)

    def delete_hud(self, monster: Monster) -> None:
        sprite = self._hud_sprites.pop(monster, None)
        if sprite:
            sprite.kill()

    def get_feet_position(self, npc: NPC, monster: Monster) -> tuple[int, int]:
        key = self.get_key(npc, monster)
        rect = self.get_rect(npc, f"monster_box_{key}")
        return rect.topleft

    def unassign(self, npc: NPC, monster: Monster) -> None:
        self._positions.pop(monster, None)
        self._layout_keys.pop((npc, monster), None)

        ui = self._monster_ui.pop(monster, None)
        if ui:
            if ui.hud_sprite:
                ui.hud_sprite.kill()
            for icon in ui.status_icons:
                icon.kill()

        logger.debug(f"[unassign] {monster.name} removed from layout and HUD")
