---
title: Rehearse mainnet contract upgrades against a testnet replica of live state
domain: stellar-soroban
tags: [soroban, upgrade, migration, defi, deployment]
source: session
date: 2026-09-05
---

## Problem
Fixing an accounting bug on a *live* mainnet vault means the fix ships as a
contract upgrade + state migration. If the migration mis-reconstructs existing
state (e.g. an outstanding liability), you corrupt real balances with no undo.

## Solution / code
Before touching mainnet:

1. Replicate current live state onto testnet.
2. Run the upgrade + `migrate_v2()` there first.
3. Have the migration **reconstruct** derived state from the on-chain source of
   truth and assert it against an independently predicted value — down to the
   smallest unit (the reconstructed liability matched prediction to the exact
   stroop).
4. Only then upgrade mainnet; balances and holders are preserved by upgrade.

## Gotchas
- The "matches to the exact stroop" check is the go/no-go signal — a migration
  that *runs* is not a migration that's *correct*.
- Non-code audit-readiness wins are the cheapest and highest-leverage: verifying
  on-chain WASM sha256 matches the repo, and moving admin custody to a multisig,
  need **no new contract code** but block a clean external-audit conversation.
- Docs drift is a security surface: a published token address that was actually
  the native asset contract, plus documented-but-unbuilt subsystems, were cut
  (~2,765 lines) and replaced with an honest *Current Limits* section.
- Pairs with [[derive-vault-accounting-from-balances]] (the fix being shipped).
