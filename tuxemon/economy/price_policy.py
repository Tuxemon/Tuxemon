# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PricePolicyData:
    discount: float | dict[str, float]
    tax: float
    fee: int
    resell_bonus: float
    resell_tax: float
    seller_fee: int


class RawPolicySchema(BaseModel):
    discount: float | dict[str, float] = Field(default=0.0)
    tax: float = Field(ge=0.0, le=1.0, default=0.0)
    fee: int = Field(ge=0, default=0)
    resell_bonus: float = Field(ge=0.0, le=1.0, default=0.0)
    resell_tax: float = Field(ge=0.0, le=1.0, default=0.0)
    seller_fee: int = Field(ge=0, default=0)


def load_policy(
    slug: str, filename: str = "price_policies.yaml"
) -> PricePolicyData | None:
    yaml_path = paths.mods_folder / filename
    raw_yaml = load_yaml(yaml_path)

    raw_data = raw_yaml.get(slug)
    if not raw_data:
        raise ValueError(f"Policy slug '{slug}' not found in {filename}")

    validated = RawPolicySchema(**raw_data)
    return PricePolicyData(
        discount=validated.discount,
        tax=validated.tax,
        fee=validated.fee,
        resell_bonus=validated.resell_bonus,
        resell_tax=validated.resell_tax,
        seller_fee=validated.seller_fee,
    )


class PricePolicy:
    """Base class for pricing policies. Override methods to customize behavior."""

    def get_discount(self, slug: str) -> float:
        return 0.0

    def get_tax_rate(self, slug: str) -> float:
        return 0.0

    def get_transaction_fee(self, slug: str) -> int:
        return 0

    def get_resell_bonus(self, slug: str) -> float:
        return 0.0

    def get_resell_tax_rate(self, slug: str) -> float:
        return 0.0

    def get_seller_fee(self, slug: str) -> int:
        return 0

    def apply_modifiers(
        self,
        base_price: int,
        quantity: int,
        slug: str,
    ) -> tuple[int, int]:
        """
        Calculates the final purchase price for an entity, applying tax, discount,
        and a transaction fee.
        """
        tax_rate = self.get_tax_rate(slug)
        discount_rate = self.get_discount(slug)
        transaction_fee = self.get_transaction_fee(slug)

        taxed_unit_price = base_price * (1 + tax_rate)

        discounted_unit_price = taxed_unit_price * (1 - discount_rate)

        if quantity == -1:
            total = discounted_unit_price + transaction_fee
        else:
            total = discounted_unit_price * quantity + transaction_fee

        final_price = round(total)

        if taxed_unit_price > 0:
            effective_discount = round(
                (1 - discounted_unit_price / taxed_unit_price) * 100
            )
        else:
            effective_discount = 0

        logger.debug(
            f"[apply_modifiers] Final Price: {final_price}, Effective Discount %: {effective_discount}"
        )

        return final_price, effective_discount

    def apply_resell_modifiers(
        self,
        base_cost: int,
        quantity: int,
        slug: str,
    ) -> tuple[int, int]:
        """
        Calculates the final amount the player receives when reselling,
        applying a bonus, a tax (fee), and a flat seller fee.
        """
        bonus_rate = self.get_resell_bonus(slug)
        tax_rate = self.get_resell_tax_rate(slug)
        seller_fee = self.get_seller_fee(slug)

        adjusted_unit_cost = base_cost * (1 + bonus_rate) * (1 - tax_rate)

        if quantity == -1:
            total = adjusted_unit_cost + seller_fee
        else:
            total = adjusted_unit_cost * quantity + seller_fee

        final_amount = max(round(total), 0)

        if base_cost > 0:
            effective_change = round(
                (adjusted_unit_cost / base_cost - 1) * 100
            )
        else:
            effective_change = 0

        logger.debug(
            f"[apply_resell_modifiers] Final Resell Price: {final_amount}, Effective % Change: {effective_change}"
        )

        return final_amount, effective_change


class StaticYamlPolicy(PricePolicy):
    def __init__(self, data: PricePolicyData) -> None:
        self._data = data
        logger.debug(f"[Init] Loaded PricePolicyData: {self._data}")

    def get_discount(self, slug: str) -> float:
        discount = self._data.discount

        if isinstance(discount, float):
            logger.debug(f"[get_discount] Slug: {slug} → {discount}")
            return discount

        if isinstance(discount, dict):
            result = discount.get(slug, discount.get("default", 0.0))
            logger.debug(f"[get_discount] Item Slug: {slug} → {result}")
            return float(result)

        logger.debug(
            f"[get_discount] Unrecognized discount format for slug: {slug}"
        )
        return 0.0

    def get_tax_rate(self, slug: str) -> float:
        logger.debug(f"[get_tax_rate] Slug: {slug} → {self._data.tax}")
        return self._data.tax

    def get_transaction_fee(self, slug: str) -> int:
        logger.debug(f"[get_transaction_fee] Slug: {slug} → {self._data.fee}")
        return self._data.fee

    def get_resell_bonus(self, slug: str) -> float:
        logger.debug(
            f"[get_resell_bonus] Slug: {slug} → {self._data.resell_bonus}"
        )
        return self._data.resell_bonus

    def get_resell_tax_rate(self, slug: str) -> float:
        logger.debug(
            f"[get_resell_tax_rate] Slug: {slug} → {self._data.resell_tax}"
        )
        return self._data.resell_tax

    def get_seller_fee(self, slug: str) -> int:
        logger.debug(
            f"[get_seller_fee] Slug: {slug} → {self._data.seller_fee}"
        )
        return self._data.seller_fee

    def apply_modifiers(
        self, base_price: int, quantity: int, slug: str
    ) -> tuple[int, int]:
        logger.debug(
            f"[StaticPolicy] Calculating Buy: {slug} (Qty: {quantity})"
        )
        result = super().apply_modifiers(base_price, quantity, slug)
        logger.debug(
            f"[StaticPolicy] Result: Price={result[0]}, Disc={result[1]}%"
        )
        return result

    def apply_resell_modifiers(
        self, base_cost: int, quantity: int, slug: str
    ) -> tuple[int, int]:
        logger.debug(
            f"[StaticPolicy] Calculating Resell: {slug} (Qty: {quantity})"
        )
        result = super().apply_resell_modifiers(base_cost, quantity, slug)
        logger.debug(
            f"[StaticPolicy] Result: Payout={result[0]}, Change={result[1]}%"
        )
        return result
