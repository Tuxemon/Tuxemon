# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace

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
