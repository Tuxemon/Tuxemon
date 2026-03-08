# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChainEvent:
    action: str
    collection: str
    owner_wallet: str
    asset_id: str
    amount_sol: float = 0.0
    metadata: dict[str, Any] | None = None


class SolanaManager:
    """Coordinates game-to-chain actions for SolaMon on Solana devnet.

    The manager can either:
    - push signed operations to an external minting service (``service_endpoint``), or
    - run in simulation mode (default) while keeping deterministic asset IDs.
    """

    def __init__(
        self,
        *,
        enabled: bool,
        rpc_url: str,
        wallet_address: str,
        treasury_address: str,
        service_endpoint: str | None,
        trainer_mint_price_sol: float,
    ) -> None:
        self.enabled = enabled
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.treasury_address = treasury_address
        self.service_endpoint = service_endpoint
        self.trainer_mint_price_sol = trainer_mint_price_sol
        self._minted_assets: dict[str, ChainEvent] = {}

    @classmethod
    def from_config(cls, config: Any) -> SolanaManager:
        return cls(
            enabled=config.enabled,
            rpc_url=config.rpc_url,
            wallet_address=config.wallet_address,
            treasury_address=config.treasury_address,
            service_endpoint=config.service_endpoint,
            trainer_mint_price_sol=config.trainer_mint_price_sol,
        )

    def mint_trainer(self, player_slug: str, player_name: str | None) -> None:
        event = ChainEvent(
            action="mint",
            collection="SolaMon Trainers",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("trainer", player_slug),
            amount_sol=self.trainer_mint_price_sol,
            metadata={"slug": player_slug, "name": player_name or player_slug},
        )
        self._submit(event)


    def mint_monster(self, monster_slug: str, instance_id: str) -> None:
        event = ChainEvent(
            action="mint",
            collection="SolaMon",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("monster", instance_id),
            metadata={"slug": monster_slug, "instance_id": instance_id},
        )
        self._submit(event)

    def burn_monster(self, instance_id: str) -> None:
        event = ChainEvent(
            action="burn",
            collection="SolaMon",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("monster", instance_id),
            metadata={"instance_id": instance_id},
        )
        self._submit(event)

    def mint_item(
        self, item_slug: str, instance_id: str, quantity: int
    ) -> None:
        event = ChainEvent(
            action="mint",
            collection="SolaMon Items",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("item", instance_id),
            metadata={
                "slug": item_slug,
                "instance_id": instance_id,
                "quantity": quantity,
            },
        )
        self._submit(event)

    def burn_item(
        self, item_slug: str, instance_id: str, quantity: int
    ) -> None:
        event = ChainEvent(
            action="burn",
            collection="SolaMon Items",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("item", instance_id),
            metadata={
                "slug": item_slug,
                "instance_id": instance_id,
                "quantity": quantity,
            },
        )
        self._submit(event)

    def mint_badge(self, badge_id: str) -> None:
        event = ChainEvent(
            action="mint",
            collection="SolaMon Badges",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("badge", badge_id),
            metadata={"badge_id": badge_id},
        )
        self._submit(event)

    def _submit(self, event: ChainEvent) -> None:
        if not self.enabled:
            return

        key = f"{event.action}:{event.asset_id}"
        if event.action == "mint" and key in self._minted_assets:
            return

        payload = asdict(event)
        payload["rpc_url"] = self.rpc_url
        payload["treasury_address"] = self.treasury_address
        payload["cluster"] = "devnet"

        if self.service_endpoint:
            self._post(payload)
        else:
            logger.info("SolaMon chain event (simulated): %s", payload)

        if event.action == "mint":
            self._minted_assets[key] = event
        elif event.action == "burn":
            self._minted_assets.pop(f"mint:{event.asset_id}", None)

    def _post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.service_endpoint or "",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as response:
                if response.status >= 400:
                    logger.error(
                        "SolaMon chain service error: %s", response.status
                    )
        except error.URLError as exc:
            logger.error("SolaMon chain service unavailable: %s", exc)

    def _asset_id(self, namespace: str, unique_key: str) -> str:
        digest = hashlib.sha256(
            f"{namespace}:{unique_key}:{self.wallet_address}".encode("utf-8")
        ).hexdigest()
        return f"solamon-{namespace}-{digest[:20]}"
