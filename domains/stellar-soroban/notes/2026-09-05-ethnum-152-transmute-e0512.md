---
title: ethnum 1.5.2 breaks Soroban WASM build with E0512 transmute error
domain: stellar-soroban
tags: [rust, soroban, cargo, ci, wasm]
source: session
date: 2026-09-05
---

## Problem
Contracts CI failed compiling a transitive dependency, not our code:

```
error[E0512]: cannot transmute between types of different sizes, or dependently-sized types
  --> ethnum-1.5.2/src/error.rs:16:14
16 |     unsafe { mem::transmute(()) }
   = note: source type: `()` (0 bits)
   = note: target type: `TryFromIntError` (8 bits)
error: could not compile `ethnum` (lib) due to 1 previous error
```

`ethnum` 1.5.2 (a transitive dep of `soroban-env-common`) does an invalid
`mem::transmute(()) -> TryFromIntError`. On current rustc this fails because
`TryFromIntError` is no longer zero-sized.

## Solution / code
Lockfile-only bump — no manifest change needed (`soroban-env-common 21.2.1`
permits it):

```bash
cargo update -p ethnum --precise 1.5.3
# verify the previously-failing crate + full release build compile for wasm:
cargo build --release --target wasm32v1-none
```

## Gotchas
- The failing crate is a **transitive** dep, so the error names `ethnum`, not
  anything you wrote — grep `Cargo.lock`, not `Cargo.toml`.
- Fix is a patch bump (1.5.2 → 1.5.3) committed in `Cargo.lock` only; keep the
  minimal-diff so the resolver doesn't drag in unrelated version churn.
- Always reproduce with the **exact CI target** (`wasm32v1-none`, `--release`);
  a native debug build may not hit the same codegen path.
- Related class of "one bad transitive crate breaks the world" — see
  [[soroban-persistent-storage-ttl]] for other Soroban build/runtime traps.
