# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

from tuxemon.solana.manager import SolanaManager


def _config(enabled: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        enabled=enabled,
        rpc_url="https://api.devnet.solana.com",
        wallet_address="wallet-abc",
        treasury_address="treasury-xyz",
        service_endpoint=None,
        trainer_mint_price_sol=0.1,
    )


def test_mint_and_burn_monster_update_cache() -> None:
    manager = SolanaManager.from_config(_config())

    manager.mint_monster("slime", "monster-1")
    assert len(manager._minted_assets) == 1

    manager.burn_monster("monster-1")
    assert len(manager._minted_assets) == 0


def test_disabled_manager_noop() -> None:
    manager = SolanaManager.from_config(_config(enabled=False))

    manager.mint_trainer("player", "Player")

    assert manager._minted_assets == {}


def test_create_devnet_wallet_from_keygen(monkeypatch) -> None:
    manager = SolanaManager.from_config(_config())
    manager.connect_wallet("")
    keygen = MagicMock(side_effect=["", "11111111111111111111111111111111"])
    monkeypatch.setattr(manager, "_run_keygen", keygen)

    ok, _ = manager.create_devnet_wallet()

    assert ok
    assert manager.wallet_address == "11111111111111111111111111111111"


def test_create_devnet_wallet_fallback_without_keygen(monkeypatch) -> None:
    manager = SolanaManager.from_config(_config())
    manager.connect_wallet("")

    monkeypatch.setattr(
        manager,
        "_run_keygen",
        MagicMock(side_effect=RuntimeError("solana-keygen missing")),
    )

    ok, _ = manager.create_devnet_wallet()

    assert ok
    assert manager.is_valid_wallet_address(manager.wallet_address)


def test_import_private_key_validation() -> None:
    manager = SolanaManager.from_config(_config())

    ok, msg = manager.import_private_key("not json")

    assert not ok
    assert "JSON array" in msg


def test_export_private_key(monkeypatch, tmp_path) -> None:
    manager = SolanaManager.from_config(_config())
    keyfile = tmp_path / "wallet.json"
    keyfile.write_text("[1,2,3]", encoding="utf-8")

    manager.connect_wallet("11111111111111111111111111111111")
    manager._wallet_keypair_files[manager.wallet_address] = keyfile
    monkeypatch.setattr(
        SolanaManager, "wallet_dir", property(lambda self: tmp_path)
    )

    ok, message = manager.export_connected_private_key()

    assert ok
    assert "Private key exported to:" in message
