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
from tuxemon.database.rules import config_monster
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.monster import Monster
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.states.quantity import QuantityPickerState
from tuxemon.states.shop_base import ShopMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


class TrainingShopConfig(BaseModel):
    background: str
    base_cost_per_level: int
    cost_scaling_type: Literal["linear", "polynomial", "exponential"] = (
        "linear"
    )
    polynomial_exponent: float | None = Field(default=1.5)


class TrainingCostPicker(QuantityPickerState):
    name: ClassVar[str] = "TrainingCostPicker"

    def __init__(
        self,
        client: BaseClient,
        trainer_state: ShopTrainingMenuState,
        monster: Monster,
        callback: Callable[[int], None],
        **kwargs: Any,
    ):
        self._trainer_state = trainer_state
        self._monster = monster
        super().__init__(client=client, callback=callback, **kwargs)

    def _compute_total(self) -> int:
        return self._trainer_state._calculate_total_training_cost(
            self._monster, self.current_value
        )


class ShopTrainingMenuState(ShopMenuState[Monster]):
    """
    A specific shop state for a training service, inheriting from the generic
    ShopMenuState. This state allows the player to pay to level up their monsters.
    """

    name: ClassVar[str] = "ShopTrainingMenuState"

    def __init__(
        self,
        client: BaseClient,
        *args: Any,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, *args, **kwargs)
        yaml_path = paths.mods_folder / "training_shop_config.yaml"
        raw_data = load_yaml(yaml_path)
        _model = model if model is not None else "cathedral"
        self.config = TrainingShopConfig(**raw_data[_model])
        self.base_cost_per_level = self.config.base_cost_per_level
        self.update_background(self.config.background)

    def _get_asset_image(self, asset: MenuItem[Monster]) -> Surface | None:
        """Returns the front sprite image for a monster."""
        renderer = MonsterRenderer(asset.game_object, scale=self.factor)
        image = renderer.get_sprite("front")
        return image.image if image else None

    def _display_asset_description(self, asset: MenuItem[Monster]) -> None:
        """Displays the monster's description."""
        if asset.description:
            self.dialog.alert(
                asset.description, self.text_area, dialog_speed="max"
            )

    def _filter_inventory(self) -> list[Monster]:
        """
        The training shop's inventory is the player's own party.
        """
        return self.applier.filter_monsters(
            self.buyer,
            self.seller,
            self.economy,
            self.client.shop_manager,
        )

    def _populate_menu(self, inventory: list[Monster]) -> None:
        """Populates the menu with the player's monsters and their training costs."""
        for monster in inventory:
            if monster.level >= config_monster.level_range[1]:
                continue  # Skip monsters already at max level

            cost = self._calculate_training_cost(monster)
            label = self._format_monster_label(monster, cost)
            unavailable = (
                cost > self.seller_manager.get_money() or monster.is_fainted
            )
            self._add_menu_item(monster, label, {"cost": cost}, unavailable)

    def _get_selection_menu_params(
        self, menu_item: MenuItem[Monster]
    ) -> dict[str, Any]:
        monster = menu_item.game_object
        available_money = self.seller_manager.get_money()

        if monster.level >= config_monster.level_range[1]:
            return {
                "callback": lambda quantity: None,
                "max_quantity": 0,
                "cost": 0,
            }

        total_cost = 0
        max_quantity = 0
        for i in range(1, config_monster.level_range[1] - monster.level + 1):
            level_cost = self._get_level_cost(monster, monster.level + i)
            if total_cost + level_cost > available_money:
                break
            total_cost += level_cost
            max_quantity = i

        def train_monster(quantity: int) -> None:
            quantity = min(
                quantity, config_monster.level_range[1] - monster.level
            )
            cost = self._calculate_total_training_cost(monster, quantity)
            if quantity > 0 and cost <= available_money:
                self.seller_manager.remove_money(cost)
                monster.set_level(monster.level + quantity, monster.level)
                self.reload_shop()

        base_cost = self._calculate_training_cost(monster)
        return {
            "callback": partial(train_monster),
            "max_quantity": max_quantity,
            "cost": base_cost,
        }

    def _calculate_total_training_cost(
        self, monster: Monster, quantity: int
    ) -> int:
        return sum(
            self._get_level_cost(monster, monster.level + i)
            for i in range(1, quantity + 1)
        )

    def _get_level_cost(self, monster: Monster, target_level: int) -> int:
        base = self.config.base_cost_per_level
        scaling = self.config.cost_scaling_type

        if scaling == "linear":
            return target_level * base
        elif scaling == "polynomial":
            exponent = self.config.polynomial_exponent or 1.5
            return int((target_level**exponent) * base)
        elif scaling == "exponential":
            return int(base * (2 ** (target_level - 1)))
        else:
            logger.warning(
                f"Unknown scaling type '{scaling}', defaulting to linear."
            )
            return target_level * base

    def _format_monster_label(self, monster: Monster, cost: int) -> str:
        return f"{monster.name} Lv.{monster.level} (${cost})"

    def _calculate_training_cost(self, monster: Monster) -> int:
        """Calculates the cost to level up a monster."""
        return self._get_level_cost(monster, monster.level + 1)

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        params = self._get_selection_menu_params(menu_monster)

        menu = TrainingCostPicker(
            client=self.client,
            trainer_state=self,
            monster=monster,
            callback=params["callback"],
            max_quantity=params["max_quantity"],
            quantity=1,
            shrink_to_items=True,
            cost=0,  # ignored
            label=lambda q: T.format(
                "shop_train_to", {"level": monster.level + q}
            ),
        )

        self.client.state_manager.push_state(menu)
