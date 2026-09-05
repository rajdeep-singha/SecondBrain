# clippers

Learnings from content-clipping work. I joined as a clipper, and this domain
collects what actually moves the needle across campaigns — hooks, formats,
platform quirks, submission rules, what gets a clip approved/paid vs rejected.

## Campaigns as tags (not subfolders)
Each campaign/brand is a lowercase `tag`, so notes stay flat and searchable and a
lesson can belong to more than one campaign. Current campaigns:

- `yahoo`
- `solana`
- `touchgrass`

Add new campaigns just by using a new tag. Every note should carry at least one
campaign tag plus concept tags (e.g. `hook`, `retention`, `tiktok`, `shorts`,
`payout`).

## How this domain works
Same pipeline as the rest of the SecondBrain: drop a raw clipper session into
`sessions/inbox/`, distill it into an atomic note here (`domains/clippers/notes/`),
then `make index`. Once there are enough repeatable patterns, this domain
graduates into a `skills/` skill (a clipper playbook) — the same "mature domains
become skills" path the repo already follows.

## Note shape
Reuse the standard `title / domain / tags / source / date` frontmatter. The
body's Problem / Solution / Gotchas headings map cleanly to
clipping: **Problem** = the campaign brief or the clip that flopped,
**Solution** = the hook/edit/format that worked, **Gotchas** = the platform or
submission rules that trip you up.
