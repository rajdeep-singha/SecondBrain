<!-- Skill catalog for skills.sh. Mirrors the skills under skills/. -->
# Skill catalog

4 skills. Install the collection or a single skill via [skills.sh](https://www.skills.sh):

```bash
npx skills add rajdeep-singha/SecondBrain                 # pick from all skills
npx skills add rajdeep-singha/SecondBrain@make-clips      # a single skill
npx skills add rajdeep-singha/SecondBrain@soroban -g      # install globally
```

Browse: https://www.skills.sh/rajdeep-singha/SecondBrain

## Clipping

### make-clips
`skills/make-clips/SKILL.md`

Cut post-ready short-form clips from a show/podcast transcript, following a fixed
set of guardrails and house style.

## Crypto engineering

### aptos-move
`skills/aptos-move/SKILL.md`

Apply accumulated Aptos Move lessons when writing, debugging, or reviewing Aptos
Move contracts — coin / fungible-asset transfers, NAV/oracle staleness guards,
off-chain keeper design, admin auth (E_NAV_STALE, E_NOT_ADMIN). Reads
`domains/aptos/notes/` as its living source.

### soroban
`skills/soroban/SKILL.md`

Apply accumulated Stellar Soroban lessons — persistent storage & TTL,
non-rebasing yield-token / vault-share design, deriving accounting from balances,
WASM build breaks (ethnum E0512), rehearsing mainnet upgrades. Reads
`domains/stellar-soroban/notes/` as its living source.

## Knowledge

### distill-session
`skills/distill-session/SKILL.md`

Distill a raw session, chat, or tweet export into an atomic, tagged note filed
under the right domain, then re-index for search. Redacts secrets and treats raw
input as untrusted (no prompt-injection follow-through).
