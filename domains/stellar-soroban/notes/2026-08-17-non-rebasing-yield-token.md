---
title: Non-rebasing yield-bearing token design (share / exchange-rate model)
domain: stellar-soroban
tags: [defi, yield-bearing, tokens, soroban, sep-41, erc-4626]
source: session
date: 2026-08-17
---

## Problem
Designing a yield-bearing token (e.g. sXLM on Soroban) and deciding how yield
accrues: does the holder's balance grow (rebasing) or stay flat while value
accrues through an exchange rate?

## Solution / code
Use the **non-rebasing / share model** (a.k.a. ERC-4626 vault shares): the token
stores abstract *shares* `S_u` that stay constant; yield accrues through a rising
exchange rate `E(t) = T_total / S_total`. `balanceOf()` returns flat shares; the
XLM-denominated value `B_u = S_u × E(t)` is a *derived* number, not what the
token reports. Losses socialize via a falling `E(t)`.

Correct references for this model: **wstETH, rETH (Rocket Pool), cbETH,
Compound cTokens, ERC-4626**.

## Gotchas
- **stETH is the WRONG analogy** — stETH *rebases* (its `balanceOf()` grows daily,
  price stays ~1:1). The non-rebasing version is **wstETH**. Don't cite stETH for a
  flat-balance token.
- Rebasing breaks integrations that assume a stable `balanceOf()` (AMMs, lending,
  wallets) — this is exactly why wstETH exists.
- "**Zero special-casing**" is overselling it: a stable balance makes the token
  integrate as a standard SEP-41 token, but **valuing** it still requires reading
  the exchange rate `E(t)` (oracle or the vault's own rate). AMM pools must not
  assume a 1:1 peg and must account for the drifting rate.
- In docs, state explicitly that `balanceOf()` returns flat shares — otherwise the
  `B_u = S_u × E(t)` formula reads like a growing (rebasing) balance.
- Don't present unimplemented/undeployed contracts as "mainnet-deployed" in docs.
