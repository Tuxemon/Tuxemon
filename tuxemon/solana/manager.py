# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import hashlib
import json
import logging
import secrets
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
        cluster: str,
        rpc_url: str,
        wallet_address: str,
        treasury_address: str,
        service_endpoint: str | None,
        trainer_mint_price_sol: float,
        official_token_mint: str,
    ) -> None:
        self.enabled = enabled
        self.cluster = cluster
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.treasury_address = treasury_address
        self.service_endpoint = service_endpoint
        self.trainer_mint_price_sol = trainer_mint_price_sol
        self.official_token_mint = official_token_mint
        self._minted_assets: dict[str, ChainEvent] = {}
        self._wallet_keypair_files: dict[str, Path] = {}

    @property
    def wallet_dir(self) -> Path:
        path = Path.home() / ".config" / "tuxemon" / "solamon_wallets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def from_config(cls, config: Any) -> SolanaManager:
        return cls(
            enabled=config.enabled,
            cluster=config.cluster,
            rpc_url=config.rpc_url,
            wallet_address=config.wallet_address,
            treasury_address=config.treasury_address,
            service_endpoint=config.service_endpoint,
            trainer_mint_price_sol=config.trainer_mint_price_sol,
            official_token_mint=config.official_token_mint,
        )

    def currency_asset(self) -> str:
        return "SOL" if self.cluster == "devnet" else self.official_token_mint

    def reward_currency(self, amount: int, reason: str) -> None:
        if amount <= 0:
            return
        event = ChainEvent(
            action="reward",
            collection="SolaMon Currency",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("currency", f"{reason}:{amount}"),
            metadata={
                "amount": amount,
                "reason": reason,
                "asset": self.currency_asset(),
            },
        )
        self._submit(event)

    def spend_currency(self, amount: int, reason: str) -> None:
        if amount <= 0:
            return
        event = ChainEvent(
            action="spend",
            collection="SolaMon Currency",
            owner_wallet=self.wallet_address,
            asset_id=self._asset_id("currency", f"{reason}:{amount}"),
            metadata={
                "amount": amount,
                "reason": reason,
                "asset": self.currency_asset(),
            },
        )
        self._submit(event)

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
            / f"solamon-devnet-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
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
            logger.warning(
                "solana-keygen unavailable, using local fallback: %s", exc
            )
            private_key = self._generate_private_key_bytes()
            wallet_file.write_text(json.dumps(private_key), encoding="utf-8")
            pubkey = self._derive_wallet_address(private_key)

        if not self.is_valid_wallet_address(pubkey):
            return False, "Generated wallet was invalid"

        self.connect_wallet(pubkey)
        self._wallet_keypair_files[pubkey] = wallet_file
        return True, f"Wallet created and connected: {pubkey}"

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
            / f"solamon-imported-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        )
        wallet_file.write_text(json.dumps(parsed), encoding="utf-8")

        try:
            pubkey = self._run_keygen(
                ["solana-keygen", "pubkey", str(wallet_file)]
            ).strip()
        except RuntimeError as exc:
            logger.warning(
                "solana-keygen unavailable, using local fallback: %s", exc
            )
            pubkey = self._derive_wallet_address(parsed)

        if not self.is_valid_wallet_address(pubkey):
            return False, "Imported key did not produce a valid wallet address"

        self.connect_wallet(pubkey)
        self._wallet_keypair_files[pubkey] = wallet_file
        return True, f"Wallet imported and connected: {pubkey}"

    def export_connected_private_key(self) -> tuple[bool, str]:
        """Export the connected wallet private key JSON to an export file."""
        wallet = self.wallet_address.strip()
        if not wallet:
            return False, "No connected wallet to export"

        source = self._wallet_keypair_files.get(wallet)
        if source is None or not source.exists():
            return (
                False,
                "Connected wallet keypair is not locally managed, cannot export.",
            )

        export_path = (
            self.wallet_dir
            / f"solamon-export-{wallet[:6]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        )
        export_path.write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return True, f"Private key exported to: {export_path}"

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
        payload["cluster"] = self.cluster

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

    def _generate_private_key_bytes(self) -> list[int]:
        """Generate a local 64-byte key-like payload for fallback mode."""
        return list(secrets.token_bytes(64))

    def _derive_wallet_address(self, private_key: list[int]) -> str:
        """Derive a deterministic, base58-like wallet string from key bytes.

        This is used as a local fallback when solana-keygen is unavailable.
        """
        digest = hashlib.sha256(bytes(private_key)).digest()
        return self._base58_encode(digest)

    def _base58_encode(self, data: bytes) -> str:
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        number = int.from_bytes(data, "big")
        encoded = ""
        while number > 0:
            number, remainder = divmod(number, 58)
            encoded = alphabet[remainder] + encoded

        leading_zeroes = 0
        for b in data:
            if b == 0:
                leading_zeroes += 1
            else:
                break
        return (alphabet[0] * leading_zeroes) + (encoded or alphabet[0])

    def _asset_id(self, namespace: str, unique_key: str) -> str:
        digest = hashlib.sha256(
            f"{namespace}:{unique_key}:{self.wallet_address}".encode("utf-8")
        ).hexdigest()
        return f"solamon-{namespace}-{digest[:20]}"
