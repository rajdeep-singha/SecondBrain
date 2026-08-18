# raw session dump — stellar soroban token, 2026-08-18

(this is an unprocessed export. Run the `distill-session` skill to turn it into a
proper note under domains/stellar-soroban/notes/, then move this file to
sessions/processed/.)

me: how do I store a per-user balance in a soroban contract in rust?
assistant: use the contract storage. Persistent storage survives across
invocations. Define a key enum and use env.storage().persistent().

we ended up with something like:

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

gotcha we hit: persistent entries need their TTL bumped or they get archived —
call env.storage().persistent().extend_ttl(...) or reads fail later. temporary
storage is cheaper but wiped, instance storage is for small global config.
