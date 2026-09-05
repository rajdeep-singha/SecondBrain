---
title: Derive vault total_assets from balances, never from a stored counter
domain: stellar-soroban
tags: [soroban, defi, vault, accounting, security]
source: session
date: 2026-09-05
---

## Problem
A live vault reported an exchange rate **5.69% higher** than it could actually
pay. Two root causes, both from *stored* state drifting away from real holdings:

- Queued withdrawals burned shares but never recorded the XLM owed → denominator
  fell while numerator didn't.
- `add_rewards()` credited a stored treasury counter without transferring XLM,
  and `withdraw_fees()` could then pay real XLM against that phantom balance
  (critical: inflates the rate with no assets behind it).

## Solution / code
Compute assets from balances on every read instead of trusting a counter:

```
total_assets = idle + deployed − pending − treasury   // all read from balances
```

Record the liability in the *same* call that burns shares. For the existing
queue, a one-shot migration reconstructed the outstanding liability from the
on-chain queue (38,114,885 stroops — matched the prediction exactly).

## Gotchas
- Every rate-manipulation finding traced back to a stored numerator that could
  diverge from real holdings — deriving from balances kills the whole **bug
  class**, not one instance.
- Any function that credits a balance must transfer the asset in the same call,
  or a later withdraw path will pay real funds against fake credit.
- This is the same "read fresh, don't trust stored" principle as
  [[nav-staleness-oracle]] (staleness guard on NAV) — pairs with
  [[rehearse-mainnet-upgrade-testnet-replica]] for safely shipping the fix.
