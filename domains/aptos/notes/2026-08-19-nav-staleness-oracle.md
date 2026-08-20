---
title: Aptos NAV staleness guard (E_NAV_STALE) and off-chain freshness
domain: aptos
tags: [move, oracle, staleness, keeper, product-design]
source: session
date: 2026-08-19
---

## Problem
Staking aborts with `E_NAV_STALE` (abort `0x6`) from a `project_token` Move
module. The stake calls `mint_to_investor`, which refuses to price the stake
because the on-chain NAV (entry price) is considered too old.

## Solution / code
The guard compares chain time against the last NAV update:

```move
// project_token.move
let now = timestamp::now_seconds();
assert!(now - state.nav_last_updated <= state.max_staleness_seconds, E_NAV_STALE);
```

`nav_last_updated` is set only at `initialize_project_token` and on every
`update_nav` call. Immediate fix: admin calls `update_nav(project_id, new_nav,
source_hash)` to reset the clock, then retry the stake within the window.

Aptos has **no on-chain cron/timers** — a contract cannot refresh itself. NAV
freshness *must* be pushed by an off-chain keeper (the `source_hash` param exists
precisely for off-chain auditability); the contract's only job is to *enforce*
that someone did it recently.

Product-design fork:
- **Slow-moving entry price** (revalued monthly/quarterly): widen
  `max_staleness_seconds` (e.g. 90 days = `7776000`) and update NAV only when the
  value truly changes. Simpler, honest, no keeper infra.
- **Live valuation**: build a real keeper that pushes genuinely recomputed values.

## Gotchas
- Re-pushing the **same** NAV number on an interval just to reset the clock
  silently turns the staleness guard into a no-op — that's security theater, not
  a keeper. If NAV rarely changes, widen the window instead.
- Init params like `max_staleness_seconds` are often fixed at init with **no
  setter** — existing deployed projects can't be changed without adding an admin
  `set_max_staleness_seconds` entry fn (or re-init).
- Widening the window with a setter does *not* touch `nav_last_updated`, so it
  immediately unblocks recently-initialized projects with no NAV refresh needed.
- `set_*` admin calls abort `E_NOT_ADMIN` if the CLI signs with the wrong
  profile — the admin is whoever called `initialize`. Match the profile to the
  server's `ADMIN_PRIVATE_KEY` account.
- `E_PROJECT_TOKEN_NOT_FOUND` means the token was never initialized on-chain for
  that project_id — off-chain `tracker.json` listings can exist with no on-chain
  token state to stake into.
