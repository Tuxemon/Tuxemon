# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import BaseModel, Field
from pygame.surface import Surface

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.monster import Monster
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.session import local_session
from tuxemon.states.quantity import QuantityPickerState
from tuxemon.states.shop_base import ShopMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


class HealingShopConfig(BaseModel):
    background: str
    base_healing_cost: int
    cost_scaling_type: Literal["linear", "polynomial", "exponential"] = (
        "linear"
    )
    polynomial_exponent: float | None = Field(default=1.5)
    exclude_if_hp_ratio_above: float = Field(default=1.0)
    revive_cost_multiplier: float = Field(default=1.0)
    revive_cost: int = Field(default=0)
    allow_fainted_monsters: bool = Field(default=True)


class HealingCostPicker(QuantityPickerState):
    name: ClassVar[str] = "HealingCostPicker"

    def __init__(
        self,
        client: BaseClient,
        healer_state: ShopHealingMenuState,
        monster: Monster,
        callback: Callable[[int], None],
        **kwargs: Any,
    ):
        self._healer_state = healer_state
        self._monster = monster
        super().__init__(client=client, callback=callback, **kwargs)

    def _compute_total(self) -> int:
        cost_per_hp = self._healer_state._get_healing_cost_per_hp(
            self._monster
        )
        total = cost_per_hp * self.current_value
        if self._monster.current_hp == 0:
            total += self._healer_state.config.revive_cost
        return total


class ShopHealingMenuState(ShopMenuState[Monster]):
    name: ClassVar[str] = "ShopHealingMenuState"

    def __init__(
        self,
        client: BaseClient,
        *args: Any,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, *args, **kwargs)
        yaml_path = paths.mods_folder / "healing_shop_config.yaml"
        raw_data = load_yaml(yaml_path)
        _model = model if model is not None else "cathedral"
        self.config = HealingShopConfig(**raw_data[_model])
        self.base_healing_cost = self.config.base_healing_cost
        self.update_background(self.config.background)

    def _get_asset_image(self, asset: MenuItem[Monster]) -> Surface | None:
        renderer = MonsterRenderer(asset.game_object, scale=self.factor)
        image = renderer.get_sprite("front")
        return image.image if image else None

    def _display_asset_description(self, asset: MenuItem[Monster]) -> None:
        if asset.description:
            self.dialog.alert(
                asset.description, self.text_area, dialog_speed="max"
            )

    def _filter_inventory(self) -> list[Monster]:
        return self.applier.filter_monsters(
            self.buyer,
            self.seller,
            self.economy,
            self.client.shop_manager,
        )

    def _populate_menu(self, inventory: list[Monster]) -> None:
        for monster in inventory:
            if monster.hp_ratio >= self.config.exclude_if_hp_ratio_above:
                continue  # HP ratio too high to be included

            if monster.is_fainted and not self.config.allow_fainted_monsters:
                continue  # Fainted monsters not allowed

            cost_per_hp = self._get_healing_cost_per_hp(monster)
            max_affordable_hp = self.seller_manager.get_money() // cost_per_hp

            # Only block if you can't afford even 1 HP
            unavailable = max_affordable_hp == 0

            estimated_total_cost = self._calculate_healing_cost(monster)
            label = self._format_monster_label(monster, estimated_total_cost)
            self._add_menu_item(
                monster, label, {"cost": estimated_total_cost}, unavailable
            )

    def _get_healing_cost_per_hp(self, monster: Monster) -> int:
        base = self.config.base_healing_cost
        scaling = self.config.cost_scaling_type

        if scaling == "linear":
            cost = base
        elif scaling == "polynomial":
            exponent = self.config.polynomial_exponent or 1.5
            cost = int((monster.level**exponent) * base)
        elif scaling == "exponential":
            cost = int(base * (2 ** (monster.level - 1)))
        else:
            logger.warning(
                f"Unknown scaling type '{scaling}', defaulting to linear."
            )
            cost = base

        # Apply revive multiplier if monster is fainted
        if monster.is_fainted:
            cost = int(cost * self.config.revive_cost_multiplier)

        return cost

    def _get_selection_menu_params(
        self, menu_item: MenuItem[Monster]
    ) -> dict[str, Any]:
        monster = menu_item.game_object
        missing_hp = monster.hp - monster.current_hp
        available_money = self.seller_manager.get_money()

        cost_per_hp = self._get_healing_cost_per_hp(monster)
        max_affordable_hp = available_money // cost_per_hp
        max_quantity = min(missing_hp, max_affordable_hp)

        def heal_monster(quantity: int) -> None:
            quantity = min(quantity, missing_hp)
            cost = quantity * cost_per_hp
            if monster.current_hp == 0:
                cost += self.config.revive_cost
            if quantity > 0 and cost <= available_money:
                self.seller_manager.remove_money(cost)
                monster.current_hp += quantity
                monster.status.clear_status(local_session)
                self.reload_shop()

        return {
            "callback": partial(heal_monster),
            "max_quantity": max_quantity,
            "cost": cost_per_hp,
        }

    def _calculate_healing_cost(self, monster: Monster) -> int:
        missing_hp = monster.hp - monster.current_hp
        cost_per_hp = self._get_healing_cost_per_hp(monster)
        total = missing_hp * cost_per_hp
        if monster.current_hp == 0:
            total += self.config.revive_cost
        return total

    def _format_monster_label(self, monster: Monster, cost: int) -> str:
        return f"{monster.name} HP: {monster.current_hp}/{monster.hp}"

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        params = self._get_selection_menu_params(menu_monster)

        menu = HealingCostPicker(
            client=self.client,
            healer_state=self,
            monster=monster,
            callback=params["callback"],
            max_quantity=params["max_quantity"],
            quantity=1,
            shrink_to_items=True,
            cost=0,  # ignored, overridden by calculate_total
            label=lambda q: T.format(
                "shop_heal_to", {"hp": min(monster.current_hp + q, monster.hp)}
            ),
        )

        self.client.state_manager.push_state(menu)
