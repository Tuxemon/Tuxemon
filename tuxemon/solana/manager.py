# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
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
    """Coordinates game-to-chain actions for SolaMon on Solana devnet."""

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

    @property
    def wallet_dir(self) -> Path:
        path = Path.home() / ".config" / "tuxemon" / "solamon_wallets"
        path.mkdir(parents=True, exist_ok=True)
        return path

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

    def has_wallet_connection(self) -> bool:
        return bool(self.wallet_address.strip())

    def connect_wallet(self, wallet_address: str) -> None:
        self.wallet_address = wallet_address.strip()

    @staticmethod
    def is_valid_wallet_address(wallet_address: str) -> bool:
        value = wallet_address.strip()
        if len(value) < 32 or len(value) > 44:
            return False
        base58_chars = (
            "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        )
        return all(c in base58_chars for c in value)

    def connect_wallet_provider(self, provider: str) -> tuple[bool, str]:
        """Connect using Phantom or Solflare through an external wallet flow."""
        provider = provider.lower().strip()
        if provider not in {"phantom", "solflare"}:
            return False, "Unsupported wallet provider"

        if self.service_endpoint:
            payload = self._post_and_read(
                {
                    "action": "wallet_connect",
                    "provider": provider,
                    "cluster": "devnet",
                    "rpc_url": self.rpc_url,
                }
            )
            wallet = str(payload.get("wallet_address", "")).strip()
            auth_url = str(payload.get("auth_url", "")).strip()
            if wallet and self.is_valid_wallet_address(wallet):
                self.connect_wallet(wallet)
                return True, f"Connected {provider.title()} wallet: {wallet}"
            if auth_url:
                try:
                    webbrowser.open(auth_url)
                except Exception as exc:
                    return False, f"Failed to open browser: {exc}"
                return (
                    True,
                    f"Opened {provider.title()} connection flow in browser.",
                )

        fallback_url = {
            "phantom": "https://phantom.app/",
            "solflare": "https://solflare.com/",
        }[provider]
        try:
            webbrowser.open(fallback_url)
        except Exception as exc:
            return False, f"Failed to open browser: {exc}"
        return (
            False,
            f"Opened {provider.title()} site. Configure service_endpoint for one-click in-game linking.",
        )

    def create_devnet_wallet(self) -> tuple[bool, str]:
        """Create a new local devnet wallet and automatically connect it."""
        if self.service_endpoint:
            payload = self._post_and_read(
                {
                    "action": "wallet_create",
                    "cluster": "devnet",
                    "rpc_url": self.rpc_url,
                }
            )
            wallet = str(payload.get("wallet_address", "")).strip()
            if wallet and self.is_valid_wallet_address(wallet):
                self.connect_wallet(wallet)
                return True, f"Created and connected wallet: {wallet}"

        wallet_file = (
            self.wallet_dir
            / f"solamon-devnet-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        )
        try:
            self._run_keygen(
                [
                    "solana-keygen",
                    "new",
                    "--no-bip39-passphrase",
                    "--silent",
                    "--outfile",
                    str(wallet_file),
                ]
            )
            pubkey = self._run_keygen(
                ["solana-keygen", "pubkey", str(wallet_file)]
            ).strip()
        except RuntimeError as exc:
            return False, str(exc)

        if not self.is_valid_wallet_address(pubkey):
            return False, "Generated wallet was invalid"

        self.connect_wallet(pubkey)
        return True, f"Wallet created and connected: {pubkey} ({wallet_file})"

    def import_private_key(self, private_key_payload: str) -> tuple[bool, str]:
        """Import private key JSON (64-byte array) and connect the wallet."""
        if self.service_endpoint:
            payload = self._post_and_read(
                {
                    "action": "wallet_import",
                    "cluster": "devnet",
                    "private_key": private_key_payload,
                }
            )
            wallet = str(payload.get("wallet_address", "")).strip()
            if wallet and self.is_valid_wallet_address(wallet):
                self.connect_wallet(wallet)
                return True, f"Imported and connected wallet: {wallet}"

        try:
            parsed = json.loads(private_key_payload)
        except json.JSONDecodeError:
            return False, "Private key must be a JSON array of integers"

        if not isinstance(parsed, list) or len(parsed) not in {32, 64}:
            return False, "Private key JSON must contain 32 or 64 bytes"

        if not all(isinstance(v, int) and 0 <= v <= 255 for v in parsed):
            return (
                False,
                "Private key bytes must be integers between 0 and 255",
            )

        wallet_file = (
            self.wallet_dir
            / f"solamon-imported-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        )
        wallet_file.write_text(json.dumps(parsed), encoding="utf-8")

        try:
            pubkey = self._run_keygen(
                ["solana-keygen", "pubkey", str(wallet_file)]
            ).strip()
        except RuntimeError as exc:
            return False, str(exc)

        if not self.is_valid_wallet_address(pubkey):
            return False, "Imported key did not produce a valid wallet address"

        self.connect_wallet(pubkey)
        return True, f"Wallet imported and connected: {pubkey}"

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

    def _post_and_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.service_endpoint or "",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
        except (error.URLError, json.JSONDecodeError):
            return {}

    def _run_keygen(self, cmd: list[str]) -> str:
        try:
            proc = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            return proc.stdout.strip()
        except FileNotFoundError as exc:
            raise RuntimeError(
                "solana-keygen is required for local wallet create/import"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                exc.stderr.strip() or "solana-keygen command failed"
            ) from exc

    def _asset_id(self, namespace: str, unique_key: str) -> str:
        digest = hashlib.sha256(
            f"{namespace}:{unique_key}:{self.wallet_address}".encode("utf-8")
        ).hexdigest()
        return f"solamon-{namespace}-{digest[:20]}"
