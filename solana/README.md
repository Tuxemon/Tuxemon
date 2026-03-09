# SolaMon Solana Program (Devnet/Mainnet-ready scaffold)

This folder contains an Anchor-based Solana program scaffold for:
- wallet-bound character state storage
- reward accounting for SOL (devnet) and SPL token rewards (mainnet)

## Quick start (devnet)

1. Install Anchor + Solana CLI.
2. `cd solana`
3. `anchor build`
4. `anchor test --skip-local-validator`
5. `anchor deploy --provider.cluster devnet`

Set `programs.localnet.solamon_state` in `Anchor.toml` after your first deploy.
