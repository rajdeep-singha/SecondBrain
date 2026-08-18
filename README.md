#  SecondBrain

A personal, domain-organized knowledge repo that **learns from my sessions and
tweets** and lets me recall it later by *meaning* — not just keyword search.

The loop:

```
raw session / tweet  ──drop──▶  inbox/  ──distill──▶  domains/<x>/notes/*.md
                                                            │
                                        ┌───────────────────┴───────────────────┐
                                        ▼                                        ▼
                             scripts/build_index.py                      scripts/embed.py
                             INDEX.md + manifest.json                    .brain/index.db
                             (browse / catalog skills)                   (semantic search)
                                                            │
                                                            ▼
                                        make search q="how did I do an aptos coin transfer?"
```

Mature domains eventually get distilled into reusable **Claude Code skills**
under `skills/`.

## Layout

| Path | What it holds |
|------|---------------|
| `domains/<domain>/notes/` | Distilled, tagged Markdown notes (the knowledge) |
| `domains/<domain>/scripts/` | Reusable code collected per domain (Move, Python, TS…) |
| `tweets/` | Distilled tweet/thread notes (`inbox/` for raw drops) |
| `sessions/inbox/` | Raw session exports waiting to be distilled |
| `skills/` | Authored/generated Claude Code skills (`SKILL.md`) |
| `scripts/` | The pipeline: `build_index.py`, `embed.py`, `search.py`, `common.py` |
| `.brain/` | Generated vector DB + state (gitignored) |
| `INDEX.md` | Generated human-readable catalog |

Domains: `aptos`, `ethereum`, `stellar-soroban`, `ai-agents`, `databases`,
`general` (cross-cutting TypeScript / React / Node / SQL). Add a new one by
creating `domains/<name>/notes/`.

## Note format (the contract)

Every note carries YAML frontmatter so both the catalog and the embedder can read it:

```markdown
---
title: Aptos coin transfer pattern
domain: aptos            # must match a domains/ subfolder (or "tweets")
tags: [move, coin, transfer]
source: session          # session | tweet | manual
date: 2026-08-18
---

## Problem
...
## Solution / code
...
## Gotchas
...
```

## Usage

```bash
make install                       # one-time: creates .venv + fastembed + sqlite-vec
make index                         # build catalog + semantic vector DB
make search q="aptos coin transfer"        # semantic recall
make search q="agent memory" d=ai-agents k=3
```

`make` auto-uses `.venv/` if present. (Homebrew's Python is externally managed,
so deps live in a project venv rather than globally.) The catalog builder
(`build_index.py`) is pure stdlib and runs with plain `python3` too.

To add knowledge: drop a raw file in `sessions/inbox/` (or `tweets/inbox/`), then
in Claude Code invoke the **`distill-session`** skill to file it as a note, and
run `make index`.

## Capturing sessions from other folders

Nothing is auto-tracked. But Claude Code already logs *every* session, in *every*
folder, to `~/.claude/projects/<encoded-path>/<session-id>.jsonl`. The importer
harvests **new** sessions from folders you allow-list:

```bash
make import-dry     # preview which sessions would be pulled
make import         # copy new in-scope sessions into sessions/inbox/
```

- Scope is controlled by **`import.allowlist`** (globs matched against each
  folder's basename — e.g. `aptos*`, `PYROS*`, `Aethera*`). Edit it to add repos.
- The importer is idempotent: already-seen sessions (tracked in
  `.brain/imported.json`) are skipped, so re-running only pulls what's new.
- Imported files are *raw* — run `distill-session` on them, then `make index`.

So working in another folder captures nothing on its own; you decide when to
`make import` and what's worth distilling.

## Systematic search

A repeatable procedure to search the brain thoroughly — freshen the index first,
then query, widen, and filter.

```bash
# 1. Make sure the index reflects the latest notes (safe to run anytime;
#    only re-embeds notes that changed).
make index

# 2. Basic semantic search (default: top 5 across all domains).
make search q="how did I do an aptos coin transfer?"

# 3. Widen the net — pull more candidates when you're exploring.
make search q="yield bearing token design" k=10

# 4. Narrow to one domain (d=<domain folder name>).
make search q="permission denied on insert" d=databases
make search q="storage TTL"                d=stellar-soroban k=3

# 5. Sweep several angles on the same topic (rephrase — semantic search
#    rewards different wording).
make search q="how do I persist per-user balance in a contract?"
make search q="contract storage archived after some time"
make search q="rebase vs exchange rate accounting"

# 6. Browse instead of search — the generated catalog, grouped by domain.
open INDEX.md          # or: less INDEX.md

# 7. Exact keyword fallback (when you know the literal term/code symbol).
grep -ri "coin::transfer" domains/ tweets/
```

Notes on the flow:
- `q=` is the query, `d=` restricts to a domain, `k=` sets how many results.
- Direct (without `make`): `.venv/bin/python scripts/search.py "query" --domain databases -k 5`.
- If search says *"no index found"*, run `make index` first.
- Scores are relative similarity, not truth — skim the top few, then open the
  linked note for the full context.

## Design notes

- **Local & key-free**: embeddings via `fastembed` (small ONNX model, CPU, no
  torch, no API keys) stored in `sqlite-vec` (a single-file embedded vector DB).
  Anthropic has no embeddings API, so local is both simplest and cheapest here.
- **`build_index.py` is stdlib-only** (`json`/`os`/`re`) — modeled on

- **Incremental**: re-embedding only touches changed notes (tracked by content hash).
