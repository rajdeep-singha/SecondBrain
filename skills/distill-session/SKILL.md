---
name: distill-session
description: Distill a raw session, chat, or tweet export into an atomic, tagged SecondBrain note filed under the right domain (aptos, ethereum, stellar-soroban, ai-agents, databases, clippers, general), then re-index for search. Use when the user says "distill", "distill this/the session", "process the inbox", "learn from this session", "learn this", "turn this into a note", "make a note from this", "save/capture this lesson", or "add this to my second brain" — or pastes a session/tweet to learn from, or points at a file in sessions/inbox or tweets/inbox.
---

# distill-session

Convert raw, messy exports into atomic, retrievable knowledge notes for the
SecondBrain repo.

## When to use
- A new file appears in `sessions/inbox/` or `tweets/inbox/`.
- The user pastes a chat/session/tweet and says "learn this" / "distill this".

## Inputs
Raw file(s) under `sessions/inbox/*.md` or `tweets/inbox/*.md`, OR text the user
pastes directly in chat.

## Domains
Notes go under `domains/<domain>/notes/` (or `tweets/` for tweet notes). Valid
domains are the subfolders of `domains/`: `aptos`, `ethereum`, `stellar-soroban`,
`ai-agents`, `databases`, `clippers`, `general`. If none fit, ask the user before
creating a new `domains/<name>/notes/` folder.

`clippers` holds content-clipping learnings; tag each note with its campaign
(e.g. `yahoo`, `solana`, `touchgrass`) rather than making per-campaign folders.
See `domains/clippers/README.md`.

## Procedure
1. **Read** the raw item fully. Identify the ONE reusable lesson (a pattern, fix,
   gotcha, or decision). If it contains several unrelated lessons, produce
   several notes — keep each note atomic (one idea per note).
2. **Classify** the domain and pick 3–6 lowercase `tags` (languages, libraries,
   concepts — e.g. `move`, `rust`, `rag`, `postgres`).
3. **Write** a note to `domains/<domain>/notes/<YYYY-MM-DD>-<slug>.md` (tweets to
   `tweets/<YYYY-MM-DD>-<slug>.md`) using the template below. Use today's date.
   Strip conversational noise; keep runnable code and the concrete gotcha.
4. **Set `source`**: `session` (from a work/chat session), `tweet`, or `manual`
   (user pasted a raw fact).
5. **Move** the processed raw file from `*/inbox/` to `*/processed/` (do not
   delete it). Skip this step if the input was pasted directly in chat.
6. **Re-index**: run `make index` (or `python scripts/build_index.py` then
   `python scripts/embed.py`) so the note is catalogued and searchable.
7. **Report** what notes you created and where.

## Note template
```markdown
---
title: <concise, searchable title>
domain: <one of the valid domains, or "tweets">
tags: [tag1, tag2, tag3]
source: session | tweet | manual
date: <YYYY-MM-DD>
---

## Problem
<the situation / what you were trying to do — 1-3 sentences>

## Solution / code
<the working approach; keep minimal runnable code>

## Gotchas
<the non-obvious traps, constraints, edge cases — this is the highest-value part>
```

## Rules
- Required frontmatter keys: `title`, `domain`, `source` (validated by `build_index.py`).
- Keep notes atomic and self-contained; a chunk of one note should make sense alone.
- Preserve exact code, commands, addresses, and version numbers from the source.
- Don't invent facts. If the raw item is ambiguous, ask the user rather than guess.
- Prefer editing/merging into an existing note over creating a near-duplicate.
