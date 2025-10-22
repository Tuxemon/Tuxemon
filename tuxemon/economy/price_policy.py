# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Union

import yaml
from pydantic import BaseModel, Field

from tuxemon.constants import paths

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PricePolicyData:
    discount: Union[float, dict[str, float]]
    tax: float
    fee: int
    resell_bonus: float
    resell_tax: float
    seller_fee: int


class RawPolicySchema(BaseModel):
    discount: Union[float, dict[str, float]] = Field(default=0.0)
    tax: float = Field(ge=0.0, le=1.0, default=0.0)
    fee: int = Field(ge=0, default=0)
    resell_bonus: float = Field(ge=0.0, le=1.0, default=0.0)
    resell_tax: float = Field(ge=0.0, le=1.0, default=0.0)
    seller_fee: int = Field(ge=0, default=0)


def load_policy(
    slug: str, filename: str = "price_policies.yaml"
) -> Optional[PricePolicyData]:
    yaml_path = paths.mods_folder / filename
    with yaml_path.open("r") as f:
        raw_yaml = yaml.safe_load(f)

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
        self, base: int, qty: int, slug: str
    ) -> tuple[int, int]:
        tax = self.get_tax_rate(slug)
        discount = self.get_discount(slug)
        fee = self.get_transaction_fee(slug)

        taxed = base * (1 + tax)
        discounted = taxed * (1 - discount)
        total = discounted + fee if qty == -1 else discounted * qty + fee
        final = round(total)
        discount_percent = round((1 - discounted / base) * 100)

        logger.debug(
            f"[apply_modifiers] Base={base}, Qty={qty}, Tax={tax}, Discount={discount}, Fee={fee}"
        )
        logger.debug(
            f"[apply_modifiers] Final={final}, Discount%={discount_percent}"
        )
        return final, discount_percent

    def apply_resell_modifiers(
        self, cost: int, qty: int, slug: str
    ) -> tuple[int, int]:
        bonus = self.get_resell_bonus(slug)
        tax = self.get_resell_tax_rate(slug)
        fee = self.get_seller_fee(slug)

        adjusted = cost * (1 + bonus) * (1 - tax)
        total = adjusted + fee if qty == -1 else adjusted * qty + fee
        final = max(round(total), 0)
        change_percent = round((adjusted / cost - 1) * 100)

        logger.debug(
            f"[apply_resell_modifiers] Cost={cost}, Qty={qty}, Bonus={bonus}, Tax={tax}, Fee={fee}"
        )
        logger.debug(
            f"[apply_resell_modifiers] Final={final}, Change%={change_percent}"
        )
        return final, change_percent


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
        self,
        base_price: int,
        quantity: int,
        slug: str,
    ) -> tuple[int, int]:
        logger.debug(
            f"[apply_modifiers] Slug: {slug}, Base Price: {base_price}, Qty: {quantity}"
        )

        tax_rate = self.get_tax_rate(slug)
        discount_rate = self.get_discount(slug)

        taxed = base_price * (1 + tax_rate)
        discounted = taxed * (1 - discount_rate)

        if quantity == -1:
            total = discounted + self.get_transaction_fee(slug)
        else:
            total = discounted * quantity + self.get_transaction_fee(slug)

        final_price = round(total)
        discounted_unit_price = discounted
        original_unit_price = base_price * (1 + tax_rate)
        effective_discount = round(
            (1 - discounted_unit_price / original_unit_price) * 100
        )

        logger.debug(
            f"[apply_modifiers] Taxed: {taxed}, Discounted: {discounted}, Fee: {self.get_transaction_fee(slug)}"
        )
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
        logger.debug(
            f"[apply_resell_modifiers] Slug: {slug}, Base Cost: {base_cost}, Qty: {quantity}"
        )

        bonus_rate = self.get_resell_bonus(slug)
        tax_rate = self.get_resell_tax_rate(slug)

        adjusted = base_cost * (1 + bonus_rate) * (1 - tax_rate)

        if quantity == -1:
            total = adjusted + self.get_seller_fee(slug)
        else:
            total = adjusted * quantity + self.get_seller_fee(slug)

        final_amount = max(round(total), 0)
        effective_change = round((adjusted / base_cost - 1) * 100)

        logger.debug(
            f"[apply_resell_modifiers] Adjusted: {adjusted}, Fee: {self.get_seller_fee(slug)}"
        )
        logger.debug(
            f"[apply_resell_modifiers] Final Resell Price: {final_amount}, Effective % Change: {effective_change}"
        )

        return final_amount, effective_change
