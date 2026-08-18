# raw session import — Aethera_Staking

- folder: `/Users/rajdeepsingha/Desktop/WORK/Aethera/Aethera_Staking`
- session: `378c9a49-498b-4e65-80e5-fd350c04252f`
- date: 2026-07-23

> Unprocessed export. Run the `distill-session` skill to file the reusable
> lessons as notes, then move this file to `sessions/processed/`.

---
**me:** look at my contracts and give me some cases to test it out , contracts are in move and in aptos chain

**claude:** I'll look at your Move contracts first, then propose test cases.

**claude:** I've read all five modules. Let me note one thing before the test list — there are a couple of **real bugs** in the flow that your tests should specifically catch, plus the standard cases. Here's the full breakdown.

## Architecture recap (the flow being tested)

`installer_registry` → `project_listing` → `state` (staking) ↔ `project_token` (FA mint/burn + yield). The interesting cross-module path is `sol_stake` → `mint_to_investor` and `sol_unstake` → `burn_from_investor`.

---

## 🐞 Bugs your tests should be designed to catch

Write these as **expected-failure or invariant** tests — they will likely fail today:

1. **`claim_rewards` and `distribute_yield` draw from *different* pots but can drain each other's accounting.** `state::claim_rewards` (line 247) pays APY rewards out of `vault_data.vault_coins` — the same pot that holds everyone's *principal*. There's no separate reward funding. Test: one user stakes, time passes, they `claim_rewards` — the vault now has less than total principal, so the *last* unstaker's `coin::extract(amount)` at `state.move:212` **aborts (insufficient coins)**. This is a principal-insolvency bug.

2. **`sol_unstake` uses one-shot full unstake but `staked_time` on a top-up resets duration for the *whole* position.** In `sol_stake` (line 147) a top-up overwrites `staked_time = current_time`, so an early small top-up re-locks the entire staked amount. Test: stake, wait near maturity, top up 1 octa, then try to unstake → `E_UNSTAKE_TOO_EARLY`.

3. **`claim_rewards` never checks `duration` and `reward_time` resets — but `sol_unstake` doesn't pay final rewards.** After unstake, `staked_amount=0` but the position/`reward_time` remain; a later `claim_rewards` computes reward on `staked_amount=0` → `E_NO_REWARD_AVAILABLE`. Confirm no rewards are silently lost/gained.

4. **Yield rounding dust locks the vault.** In `distribute_yield` (line 271) integer division floors `cumulative_yield_per_token`; summed claims can slightly undershoot deposited APT, leaving dust permanently trapped in `yield_vault` (no admin sweep exists). Worth an explicit accounting test.

5. **`admin_force_burn` decrements `total_supply` but not the investor's staked `tokens_minted`.** After a force-burn, `sol_unstake` tries to `burn_from_investor(tokens_minted)` but the balance is now short → `E_INSUFFICIENT_BALANCE`, bricking that user's unstake. Test the force-burn-then-unstake sequence.

---

## ✅ Test cases by module

### `installer_registry`
- **Happy:** register → submit_kyc → approve_kyc; `is_kyc_approved` true.
- register twice → `E_ALREADY_REGISTERED`.
- submit_kyc before register → `E_NOT_REGISTERED`.
- submit_kyc twice (resubmit) → `E_KYC_NOT_SUBMITTED`.
- approve_kyc when status is PENDING (not SUBMITTED) → `E_KYC_NOT_SUBMITTED`.
- non-admin calls approve_kyc / reject_kyc → `E_NOT_ADMIN`.
- **Edge:** `reject_kyc` has no status guard — reject an already-APPROVED installer succeeds and silently revokes them. Verify that's intended.

### `project_listing`
- **Happy:** approved installer `submit_project` → id starts at 1, increments; `set_project_id` writes back to installer.
- submit_project by non-KYC-approved installer → `E_KYC_NOT_APPROVED`.
- approve/reject/set_token_params by non-admin → `E_NOT_ADMIN`.
- set_token_params on a PENDING or REJECTED project → `E_NOT_APPROVED`.
- set_token_params on nonexistent id → `E_PROJECT_NOT_FOUND`.
- **Edge:** approve then reject then approve — status is freely mutable, no state-machine guard. Confirm reject-after-approve is allowed by design.
- **Edge:** two projects by the *same* installer — `set_project_id` overwrites the first id in installer record. Verify that's acceptable.

### `project_token`
- **Init:** `initialize` then `initialize_project_token` twice for same id → `E_PROJECT_TOKEN_EXISTS`.
- initialize_project_token by non-admin → `E_NOT_ADMIN`.
- **Lifecycle:** `set_lifecycle` must be strictly increasing → setting equal or lower → `E_INVALID_LIFECYCLE`; > CLOSED (5) → `E_INVALID_LIFECYCLE`.
- **NAV:** `update_nav` to 0, then mint → `E_NAV_ZERO`.
- **NAV staleness:** advance time past `max_staleness_seconds`, mint → `E_NAV_STALE`. (Note: `now - nav_last_updated` — set staleness so boundary `==` passes, `+1` fails.)
- **Mint math:** stake `apt_amount < nav` → returns 0, no tokens, no `UserYieldState` entry created; stake exactly `nav` → 1 token; stake `2.5*nav` → 2 tokens (integer floor), 0.5 remainder still staked as principal.
- **Mint lifecycle guard:** mint in PRE_LAUNCH or MATURED/CLOSED → `E_WRONG_LIFECYCLE` (only FUNDING/ACTIVE allowed).
- **max_supply:** set a cap, mint beyond it — does the FA `mint` abort? `total_supply` is tracked manually but the FA has its own max; confirm behavior at the cap boundary.
- **distribute_yield:** in wrong lifecycle (FUNDING) → `E_WRONG_LIFECYCLE`; with `total_supply==0` → `E_ZERO_SUPPLY`; amount 0 → `E_ZERO_AMOUNT`.
- **Yield fairness (the core accumulator test):** 
  - User A stakes (gets tokens) → admin `distribute_yield` → User B stakes → B's snapshot = current accumulator → `distribute_yield` again → A can claim share of *both*, B only the *second*. Assert exact amounts.
  - Claim twice in a row → second → `E_NO_YIELD`.
  - claim_yield with no `UserYieldState` → `E_NO_YIELD`.
- **claim_yield after transferring FA away:** yield is computed on *live balance*, not staked amount — transfer tokens to a third party, then the recipient can `claim_yield` (they have balance + ... actually no UserYieldState). Test: does someone who *received* tokens via transfer (never staked) get yield? They have no snapshot → `E_NO_YIELD`. But the original staker's pending yield drops because their balance dropped. Verify this "yield follows balance, entitlement follows snapshot" interaction.
- **burn_from_investor secondary-market guard:** mint, transfer tokens away, then `sol_unstake` → `burn_from_investor` sees `balance < amount` → `E_INSUFFICIENT_BALANCE`.
- **admin_force_burn:** amount 0 → `E_ZERO_AMOUNT`; amount > total_supply → `E_INSUFFICIENT_BALANCE`; happy path pulls from holder store via transfer_ref without holder signature.

### `state` (staking) — integration
- **Full happy path:** initialize hub → create_project_vault → set token to FUNDING → sol_stake → assert `get_player_tokens_minted` matches `amount/nav` → set ACTIVE → distribute_yield → claim_yield → advance time → sol_unstake (burns tokens, returns principal).
- create_project_vault by non-admin → `E_NOT_ADMIN`; duplicate vault → `E_VAULT_ALREADY_EXISTS`.
- deposit / sol_stake / unstake on nonexistent vault → `E_VAULT_NOT_FOUND`.
- sol_stake amount 0 → `E_AMOUNT_ZERO`.
- sol_unstake before `duration` elapses → `E_UNSTAKE_TOO_EARLY`; unstake with no stake → `E_NOT_STAKED`.
- **Double unstake:** unstake, then unstake again → second sees `staked_amount=0`, `tokens_minted=0` — `burn` is skipped, principal extract of 0. Confirm it doesn't abort or double-refund.
- claim_rewards with `elapsed_time` too small so reward floors to 0 → `E_NO_REWARD_AVAILABLE`.
- **withdraw drains vault:** admin `withdraw` empties `vault_coins` including staked principal → subsequent user `sol_unstake` aborts on `coin::extract`. Insolvency test (admin rug vector — confirm intended access).
- **Mint-but-zero-tokens stake:** stake `< nav`, then unstake — `tokens_minted==0` so no burn, principal returned. Good regression case.

---

## Suggested scaffolding

Want me to generate an actual `tests/` Move file with `#[test]` / `#[expected_failure(abort_code = ...)]` functions using `aptos_framework::account::create_account_for_test` and `timestamp::set_time_has_started_for_testing`? I can wire up the fixtures (admin, installer, two investors, funded AptosCoin via `aptos_coin::initialize_for_test`) and implement, say, the yield-fairness test and the top-up-relock bug test first. Just say which subset to start with.

Which do you want next?

**me:** No I need commands to test my contracts here the main contracts , as they are in testnet so no issues

**claude:** Let me check your Aptos CLI config so I can give you commands with the right addresses/profiles.

**claude:** Everything is published under the `testnet_v2` profile (account `0x863020…` = your `aethera_staking` address). Your `default` profile (`0x389448…`) is a separate funded account — perfect to act as installer/investor.

Let me quickly check what's already initialized on-chain so I don't hand you commands that abort with `RESOURCE_ALREADY_EXISTS`.

**claude:** Nothing is initialized yet — clean slate. Here's the full end-to-end test sequence. All the `*_authority` addresses are the admin address (that's where every resource gets stored).

## Setup — paste this once

```bash
cd /Users/rajdeepsingha/Desktop/WORK/Aethera/Aethera_Staking

# Roles
export ADMIN=0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1   # profile: testnet_v2 (publisher/admin)
export INV=0x3894481b4dab10b691e954de7836b39fab6ea587861a613792aabd2f21008747     # profile: default   (installer + investor)
export M=$ADMIN::                 # module prefix, e.g. ${M}state::sol_stake
export PID=1                      # first project_id

# Fund both accounts on testnet
aptos account fund-with-faucet --account $ADMIN --profile testnet_v2
aptos account fund-with-faucet --account $INV  --profile default
```

Params I picked so the math is clean: **nav = 1 APT (1e8 octas) → 1 token per APT**, staleness = 1 year, duration = 0 (unstake immediately), apy = 10%.

## 1. Initialize the four modules (admin)

```bash
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}installer_registry::initialize

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::initialize \
  --args address:$ADMIN                 # registry_authority = InstallerRegistry addr

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::initialize \
  --args address:$ADMIN                 # project_authority = ProjectRegistry addr

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}state::initialize \
  --args address:$ADMIN address:$ADMIN  # project_authority, token_hub_authority
```

## 2. Installer + KYC + project listing

```bash
# Installer registers (as INV / default profile)
aptos move run --profile default --assume-yes \
  --function-id ${M}installer_registry::register_installer \
  --args address:$ADMIN string:"Phoenix Solar" string:"BR-12345"

# Installer submits KYC docs + location
aptos move run --profile default --assume-yes \
  --function-id ${M}installer_registry::submit_kyc \
  --args address:$ADMIN string:"ipfs://kycdocs" u64:101

# Admin approves KYC
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}installer_registry::approve_kyc \
  --args address:$ADMIN address:$INV

# Installer submits a project (becomes project_id 1)
aptos move run --profile default --assume-yes \
  --function-id ${M}project_listing::submit_project \
  --args address:$ADMIN string:"Phoenix-01" u64:101 u64:500 u64:1000000000 \
         string:"Solar farm" string:"ipfs://docs" u64:800

# Admin approves project, then sets token economics
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::approve_project \
  --args address:$ADMIN u64:$PID

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::set_token_params \
  --args address:$ADMIN u64:$PID string:"AETH-PHOENIX-01" u64:60 u64:100000000
```

## 3. Stand up the token + vault, open funding

```bash
# Create the FA:  max_supply=0 (uncapped), nav=1e8 octas, staleness=1yr
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::initialize_project_token \
  --args address:$ADMIN u64:$PID u64:0 u64:100000000 u64:31536000

# Lifecycle 0->1 (FUNDING) so minting is allowed
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::set_lifecycle \
  --args address:$ADMIN u64:$PID u8:1

# Staking vault, apy_rate = 10
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}state::create_project_vault \
  --args address:$ADMIN u64:$PID u64:10
```

## 4. Stake → auto-mint tokens (investor)

```bash
# Stake 5 APT (500000000 octas), duration=0  -> mints 5 tokens
aptos move run --profile default --assume-yes \
  --function-id ${M}state::sol_stake \
  --args address:$ADMIN u64:$PID u64:500000000 u64:0
```

## 5. Yield: go ACTIVE, distribute, claim (admin then investor)

```bash
# 1->2 (ACTIVE) so distribute/claim are allowed
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::set_lifecycle \
  --args address:$ADMIN u64:$PID u8:2

# Admin distributes 2 APT of yield (funded from admin wallet into the project vault)
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::distribute_yield \
  --args address:$ADMIN u64:$PID u64:200000000

# Investor claims their APT yield
aptos move run --profile default --assume-yes \
  --function-id ${M}project_token::claim_yield \
  --args address:$ADMIN u64:$PID
```

## 6. Unstake → burns the staked tokens, returns principal

```bash
aptos move run --profile default --assume-yes \
  --function-id ${M}state::sol_unstake \
  --args address:$ADMIN u64:$PID
```

## View / assert helpers (no gas, use for checking state between steps)

```bash
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle        --args address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_nav              --args address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_token_total_supply --args address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_token_balance    --args address:$INV address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_pending_yield     --args address:$INV address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_treasury_state    --args address:$ADMIN u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}state::get_player_stake              --args address:$INV u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}state::get_player_tokens_minted      --args address:$INV u64:$PID
aptos move view --profile testnet_v2 --function-id ${M}installer_registry::get_kyc_status   --args address:$ADMIN address:$INV
aptos move view --profile testnet_v2 --function-id ${M}project_listing::get_project_status  --args address:$ADMIN u64:$PID
```

## Negative tests (these SHOULD abort — that's the pass condition)

```bash
# NAV=0 then stake -> E_NAV_ZERO (7). Run update_nav to 0 first:
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}project_token::update_nav \
  --args address:$ADMIN u64:$PID u64:0 string:"hash"   # then a sol_stake should abort 7

# Non-admin tries to distribute yield -> E_NOT_ADMIN (1)
aptos move run --profile default --assume-yes --function-id ${M}project_token::distribute_yield \
  --args address:$ADMIN u64:$PID u64:100

# Lifecycle going backward -> E_INVALID_LIFECYCLE (4)
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}project_token::set_lifecycle \
  --args address:$ADMIN u64:$PID u8:1

# Stake < 1 NAV (e.g. 50000000 = 0.5 APT) -> succeeds but mints 0 tokens (get_token_balance unchanged)
aptos move run --profile default --assume-yes --function-id ${M}state::sol_stake \
  --args address:$ADMIN u64:$PID u64:50000000 u64:0

# Duplicate vault -> E_VAULT_ALREADY_EXISTS (7)
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}state::create_project_vault \
  --args address:$ADMIN u64:$PID u64:10
```

A few notes:
- **Order matters** for lifecycle: minting needs stage 1 or 2; `distribute_yield`/`claim_yield` need stage 2 or 3. Run step 5 before undoing NAV in the negative tests.
- If you want a **second independent investor**, add a third profile with `aptos init --profile inv2 --network testnet`, fund it, and reuse the same commands with `--profile inv2` — that's the setup needed to actually verify the yield-accumulator fairness bug I flagged (A stakes → distribute → B stakes → distribute → compare claims).
- Want me to drop all of this into a runnable `scripts/testnet_e2e.sh` with the view-assertions inline so you can run the whole flow in one shot?

**me:** aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle        --args address:$ADMIN u64:$PID
error: invalid value 'project_token::get_lifecycle' for '--function-id <FUNCTION_ID>': Invalid arguments: FunctionId is not well formed.  Must be of the form <address>::<module>::<function>

For more information, try '--help'.

**claude:** `$M` is empty in your current shell — the error shows it expanded to just `project_token::get_lifecycle`, so the address prefix is missing. The `export` block from setup didn't run in this same terminal session (new tab, or it wasn't executed).

Re-run the exports, then the command:

```bash
export ADMIN=0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1
export INV=0x3894481b4dab10b691e954de7836b39fab6ea587861a613792aabd2f21008747
export M=$ADMIN::
export PID=1
```

Verify it's set (should print the full `0x8630…::`):

```bash
echo "$M"
```

Then run the view:

```bash
aptos move view --profile testnet_v2 \
  --function-id ${M}project_token::get_lifecycle \
  --args address:$ADMIN u64:$PID
```

Or if you just want to skip the variables entirely, paste the address inline:

```bash
aptos move view --profile testnet_v2 \
  --function-id 0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1::project_token::get_lifecycle \
  --args address:0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1 u64:1
```

Note: `export` only lives for the current terminal session. If you open a new tab or the exports scrolled off, set them again. To make them permanent, add the four `export` lines to your `~/.zshrc`.

**me:** why should i run export

**claude:** Because `$M`, `$ADMIN`, `$PID` are **shell variables** — they only exist if you define them in that specific terminal session. When you write `${M}project_token::get_lifecycle`, the shell substitutes whatever `M` holds *before* running the command. If `M` was never set (or you opened a new terminal tab), it expands to an empty string, so the command becomes `project_token::get_lifecycle` — missing the address — which is exactly the error you got.

Three things about them:

1. **They're per-session.** `export M=...` lives only in that one terminal window. Close it, open a new tab, or the session resets → the variable is gone and you're back to empty expansion.
2. **They're just a convenience.** The address `0x863020…771e1` is long and appears in every command. The variable lets you type `${M}` instead of pasting 66 hex characters each time. That's the only reason they exist — the contract doesn't care.
3. **`export` vs plain `M=...`** — `export` makes the variable visible to programs the shell launches (like `aptos`). For pure text substitution in the command line you technically don't even need `export`; plain `M=0x8630...::` works too, since the shell substitutes it before `aptos` ever runs.

So you have two equally valid choices:

**Use variables** (less typing, but must set them once per terminal session):
```bash
export M=0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1::
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle --args address:0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1 u64:1
```

**Skip variables entirely** — paste the full address every time (nothing to set up, just longer commands):
```bash
aptos move view --profile testnet_v2 --function-id 0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1::project_token::get_lifecycle --args address:0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1 u64:1
```

Both do the identical thing. If you don't want to think about `export` at all, just use the second form.

**me:** aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle        --args address:$ADMIN u64:$PID                                                   
{
  "Error": "API error: API error Error(InvalidInput): Failed to borrow global resource from 863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1"
}

**claude:** That error means the `ProjectTokenHub` resource doesn't exist at the admin address yet — i.e. you haven't run the initialization commands. The view is trying to `borrow_global<ProjectTokenHub>` and finding nothing there.

Good news: your variables are working now (the function-id expanded correctly this time). You just skipped ahead to step 6's view before running steps 1–3 that actually create the resources.

Let me confirm what's on-chain right now:

**claude:** Confirmed — **none of the modules are initialized on-chain yet.** All four resources are still 404. That's why the view fails: there's no `ProjectTokenHub` to read from.

The view commands only work *after* you've created the data. You need to run the setup steps in order first. Here's the minimum path to make that specific `get_lifecycle` view return something:

1. **Step 1** — initialize all four modules (creates the hub resources)
2. **Step 2** — installer/KYC/listing (so a project with token params exists)
3. **Step 3** — `initialize_project_token` (adds project_id 1 into the hub's table)

Only then does `get_lifecycle(admin, 1)` have a lifecycle value to return (it'll be `0` = PRE_LAUNCH right after init).

So go back and run the commands starting from **"## 1. Initialize the four modules"** through at least step 3, in order. The `run` commands (which cost gas and change state) are what create everything; the `view` commands only *read* what those created.

Quick way to check progress as you go — after step 1 you can re-run my curl check, or just try the view again after step 3.

Want me to bundle steps 1–6 into a single `scripts/testnet_e2e.sh` that runs each command in order and prints the view results between them? Then you run one script instead of pasting 15 commands and won't hit ordering issues.

**me:** already deployed Transaction submitted: https://explorer.aptoslabs.com/txn/0x82d5d060463ee22efa0f45605331751078cdd7fc00b0125d236b2ae7c413d8dd?network=testnet
{
  "Result": {
    "transaction_hash": "0x82d5d060463ee22efa0f45605331751078cdd7fc00b0125d236b2ae7c413d8dd",
    "gas_used": 1288,
    "gas_unit_price": 100,
    "sender": "863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1",
    "sequence_number": 1,
    "replay_protector": {
      "SequenceNumber": 1
    },
    "success": true,
    "timestamp_us": 1784774217382464,
    "version": 10100389630,
    "vm_status": "Executed successfully"
  }
} . still  aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle        --args address:$ADMIN u64:$PID
{
  "Error": "API error: API error Error(InvalidInput): Failed to borrow global resource from 863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1"
}

**claude:** Publishing the module ≠ calling `initialize`. That transaction was likely the module publish (or one init call), but the `ProjectTokenHub` resource still needs `project_token::initialize` to be run. Let me check what exists right now:

**claude:** That's the key distinction: **the module code is published, but its state isn't initialized.**

- **Deploy/publish** = uploading the compiled code. ✅ Done.
- **`initialize`** = calling the entry function that actually creates the `ProjectTokenHub` resource (the storage `move_to`s the hub to your address). ❌ Not done yet.

The transaction you pasted (`sequence_number: 1`) was the publish. Publishing code doesn't run any function — it just makes the functions *callable*. You still have to call each `initialize` yourself.

So `get_lifecycle` fails because there's no hub resource to read, and even after you create it, project_id 1 won't exist in its table until `initialize_project_token` runs.

**Run these now, in order** (the four inits create the resources):

```bash
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}installer_registry::initialize

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::initialize \
  --args address:$ADMIN

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::initialize \
  --args address:$ADMIN

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}state::initialize \
  --args address:$ADMIN address:$ADMIN
```

After the third one, this will stop erroring (returns `0` = PRE_LAUNCH… actually it'll still error until the project exists — see below):

```bash
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_lifecycle --args address:$ADMIN u64:$PID
```

Note `get_lifecycle` asserts `project_id` exists in the table, so it keeps returning `E_PROJECT_TOKEN_NOT_FOUND` until you complete **steps 2 and 3** (KYC → submit_project → approve → set_token_params → `initialize_project_token`). Right after `project_token::initialize` you can instead confirm the hub exists with:

```bash
aptos move view --profile testnet_v2 --function-id ${M}project_token::get_treasury_state --args address:$ADMIN u64:$PID
```

(still needs the project) — or just re-run my curl check and you'll see `ProjectTokenHub: EXISTS`.

Want me to write the one-shot `scripts/testnet_e2e.sh` so you don't have to babysit the ordering? It'll run all inits + the listing flow + token setup + a stake, printing views between steps.

**me:** okay which one should I innitialize , as innitializing won't hurt when I am integrating and testing with backend

**claude:** Run **all four — each exactly once.** They're not optional; each one creates the resource that a different part of your backend flow reads from. And they wire the modules together via the authority addresses, so the order/args matter.

One caution: `initialize` is **not** re-runnable. Calling it a second time aborts with `RESOURCE_ALREADY_EXISTS` (each does a `move_to`). So "initializing won't hurt" is only true the *first* time — run each once and never again (unless you republish to a fresh address).

Here's what each one does and why you need it:

| # | Command | Creates | Needed for |
|---|---------|---------|-----------|
| 1 | `installer_registry::initialize` | `InstallerRegistry` | KYC / installer onboarding |
| 2 | `project_listing::initialize` (arg: registry addr) | `ProjectRegistry` | Listing projects; reads KYC from #1 |
| 3 | `project_token::initialize` (arg: project-registry addr) | `ProjectTokenHub` | Minting/yield; reads token params from #2 |
| 4 | `state::initialize` (args: project-registry addr, token-hub addr) | `StakingHub` | Staking; calls into #3 to mint/burn |

Since your admin is a single account (`$ADMIN`), every authority address is just `$ADMIN`. Run them in this order:

```bash
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}installer_registry::initialize
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}project_listing::initialize --args address:$ADMIN
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}project_token::initialize   --args address:$ADMIN
aptos move run --profile testnet_v2 --assume-yes --function-id ${M}state::initialize           --args address:$ADMIN address:$ADMIN
```

The order matters only because #2 stores a pointer to #1, #3 to #2, and #4 to #2+#3 — but since they all point at the same `$ADMIN` address, you could technically run them in any order and it'd still resolve. Doing them 1→4 is just the clean mental model.

After these four, the resources exist and your backend can start calling entry functions. But remember: **initializing the modules ≠ having a project.** For `get_lifecycle`/staking to work you still need the per-project setup (KYC → submit_project → approve → set_token_params → `initialize_project_token` → `create_project_vault`). That per-project flow *is* re-runnable for each new `project_id`.

Want me to verify all four landed once you run them?

**me:** Now all view function will work ?

**claude:** No — initializing the four hubs makes the **resources exist**, but most views also assert that a specific `project_id` / installer / vault exists *inside* those hubs. Those still abort until you create the underlying data.

Two groups:

**✅ Work immediately after the 4 inits** (they return a default instead of asserting):
- `project_listing::is_project_approved` → `false`
- `installer_registry::is_kyc_approved` → `false`
- `state::get_player_stake` → `0`
- `state::get_player_tokens_minted` → `0`

**❌ Still abort until the data exists** (they do `assert!(contains(...))` first):

| View | Needs first | Error until then |
|------|-------------|------------------|
| `project_token::get_lifecycle` / `get_nav` / `get_token_total_supply` / `get_treasury_state` / `get_token_balance` / `get_pending_yield` | `initialize_project_token` (project in hub table) | `E_PROJECT_TOKEN_NOT_FOUND` |
| `project_listing::get_project_status` / `get_project_cost` / `get_project_location` / `get_expected_yield` | `submit_project` | `E_PROJECT_NOT_FOUND` |
| `state::get_project_total_staked` / `get_project_apy` | `create_project_vault` | `E_VAULT_NOT_FOUND` |
| `installer_registry::get_kyc_status` / `get_installer_location` | `register_installer` | `E_NOT_REGISTERED` |

So the rule of thumb: **a view works once the thing it's looking up has been created.** `get_lifecycle` for project 1 works only after `initialize_project_token` for project 1.

This isn't a bug — it's the intended "does this key exist in the table" guard. Your backend should either catch that abort or call the `is_*`/`get_player_*` views (which return defaults) to check existence first.

To make the whole set light up, run the per-project flow: `register_installer` → `submit_kyc` → `approve_kyc` → `submit_project` → `approve_project` → `set_token_params` → `initialize_project_token` → `create_project_vault`. After that, every view for project 1 returns real data.

Want me to write the one-shot script that runs inits + this full project setup so all views go green in one go?

**me:** Innitialized now : aptos move view --profile testnet_v2 --function-id ${M}project_token::get_pending_yield     --args address:$INV address:$ADMIN u64:$PID
{
  "Error": "API error: API error Error(InvalidInput): Move abort in 0x863020b97851d89a4a208c4b5d790031fe4d28e7c802d17bbf95284668f771e1::project_token: E_PROJECT_TOKEN_NOT_FOUND(0x3): "
}

**claude:** That's exactly the expected next step — and it's progress. Notice the error changed: no more "Failed to borrow global resource" (the hub now exists), it's now `E_PROJECT_TOKEN_NOT_FOUND(0x3)`. That means the hub is initialized but **project 1 isn't in its table yet.**

`get_pending_yield` looks up project 1 in the hub and asserts it exists → you need to run `initialize_project_token` for project 1. But that call reads token params from `project_listing`, which requires the project to have been submitted, approved, and had its token params set. So the full chain to make this view work:

```bash
# --- installer + KYC (INV = installer) ---
aptos move run --profile default --assume-yes \
  --function-id ${M}installer_registry::register_installer \
  --args address:$ADMIN string:"Phoenix Solar" string:"BR-12345"

aptos move run --profile default --assume-yes \
  --function-id ${M}installer_registry::submit_kyc \
  --args address:$ADMIN string:"ipfs://kycdocs" u64:101

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}installer_registry::approve_kyc \
  --args address:$ADMIN address:$INV

# --- project listing (becomes project_id 1) ---
aptos move run --profile default --assume-yes \
  --function-id ${M}project_listing::submit_project \
  --args address:$ADMIN string:"Phoenix-01" u64:101 u64:500 u64:1000000000 \
         string:"Solar farm" string:"ipfs://docs" u64:800

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::approve_project \
  --args address:$ADMIN u64:$PID

aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_listing::set_token_params \
  --args address:$ADMIN u64:$PID string:"AETH-PHOENIX-01" u64:60 u64:100000000

# --- THIS is what adds project 1 to the token hub table ---
aptos move run --profile testnet_v2 --assume-yes \
  --function-id ${M}project_token::initialize_project_token \
  --args address:$ADMIN u64:$PID u64:0 u64:100000000 u64:31536000
```

After that last command, retry your view:

```bash
aptos move view --profile testnet_v2 \
  --function-id ${M}project_token::get_pending_yield \
  --args address:$INV address:$ADMIN u64:$PID
```

It'll return `0` (investor hasn't staked yet, so no yield accrued) instead of aborting.

Reminder from before: each of these is **not** re-runnable per project — `register_installer` twice → `E_ALREADY_REGISTERED`, `initialize_project_token` twice → `E_PROJECT_TOKEN_EXISTS`, etc. Run each once. If any step aborts because you already ran it, just skip it and continue.

The ordering pain is exactly why I keep offering — want me to write `scripts/testnet_e2e.sh` that runs this whole chain top to bottom with the views printed in between? One command instead of hand-feeding these.
