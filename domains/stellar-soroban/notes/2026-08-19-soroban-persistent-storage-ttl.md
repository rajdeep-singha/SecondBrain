---
title: Per-user balances in Soroban use persistent storage, and TTL must be bumped
domain: stellar-soroban
tags: [rust, soroban, storage, ttl, smart-contracts]
source: session
date: 2026-08-19
---

## Problem
Store a per-user (per-`Address`) balance inside a Soroban contract in Rust, and
have it survive across contract invocations.

## Solution / code
Use `env.storage().persistent()` keyed by a `#[contracttype]` enum. Persistent
storage survives across invocations (unlike temporary storage).

```rust
#[contracttype]
pub enum DataKey { Balance(Address) }

pub fn balance(env: Env, id: Address) -> i128 {
    env.storage().persistent().get(&DataKey::Balance(id)).unwrap_or(0)
}

pub fn set_balance(env: Env, id: Address, amount: i128) {
    env.storage().persistent().set(&DataKey::Balance(id), &amount);
}
```

## Gotchas
- Persistent entries get **archived** if their TTL expires — later reads then
  fail. Bump it with `env.storage().persistent().extend_ttl(...)` on write/read.
- Pick the storage tier deliberately: **persistent** = per-key durable state
  (balances); **temporary** = cheaper but wiped (fine for ephemeral data);
  **instance** = small global contract config, shares the contract's TTL.
