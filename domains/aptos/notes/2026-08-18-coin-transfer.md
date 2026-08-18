---
title: Aptos coin transfer pattern
domain: aptos
tags: [move, coin, transfer, entry-function]
source: session
date: 2026-08-18
---

## Problem
Move a fungible `Coin<T>` from a signer to another address in an Aptos Move
module, exposed as a callable entry function.

## Solution / code
Use the framework `coin` module. `coin::transfer` handles withdraw + deposit and
aborts if the sender is not registered for the coin or has insufficient balance.

```move
module my_addr::payments {
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;

    /// Transfer `amount` octas of APT from `from` to `to`.
    public entry fun send_apt(from: &signer, to: address, amount: u64) {
        coin::transfer<AptosCoin>(from, to, amount);
    }
}
```

The recipient must have registered the coin store (`coin::register<AptosCoin>`)
or the deposit aborts, unless the coin allows implicit registration.

## Gotchas
- Amounts are in the coin's smallest unit — APT uses **octas** (1 APT = 1e8 octas).
- `coin::transfer` aborts on insufficient balance; there is no boolean return.
- For arbitrary fungible assets prefer the newer `fungible_asset` / `primary_fungible_store` APIs over legacy `coin`.
