---
name: make-clips
description: Cut post-ready short-form clips from a show/podcast transcript, following a fixed set of guardrails and house style. Use when the user says "make clips", "cut clips", "clip this", "clip the transcript/episode", "find clips", "give me clips", points at a transcript in a Clippings campaign folder (Yahoo, Solana, Touchgrass, or a new one), or asks to extract the best/viral/hot-take moments from a transcript. Distilled from the clippers domain — see domains/clippers/notes/.
---

# make-clips

Turn a raw episode transcript into a ranked list of catchy, self-contained,
post-ready clips with verbatim quotes and timestamps.

## When to use
- A transcript (`.txt`/`.srt`/`.vtt`) lands in a campaign folder under
  `~/Desktop/Clippings/<Campaign>/` (Yahoo, Solana, Touchgrass, …), or the user
  pastes one and says "clip this / make clips / find the best moments".

## Inputs
The transcript, plus (if known) the show name and host/guest. If the target
editor is Canva and frame-accurate cuts matter, ask up front for a **word-level
transcript** (`.srt`/`.vtt`) or the audio/video — block-level transcripts can't
give exact end times.

## Procedure
1. **Read the whole transcript** before cutting anything. Sweep for every catchy
   moment, including spicy / hot-take / contrarian segments — don't stop at the
   first few.
2. **Identify the speakers by content**, not by the raw "Speaker N" labels (they
   lie/swap). The cast changes every episode: get names from the intro or ask the
   user. A solo show attributes everything to the one host.
3. **Select** only segments that are catchy AND worth posting (see Selection).
4. **Verify length** on each: `end − start ≥ 60s`. If short, extend to the nearest
   sentence boundary. If it can't reach 60s, log it under "Not shipped" — never
   silently drop a viral-but-short moment.
5. **Write** the clips file to `~/Desktop/Clippings/<Campaign>/<slug>-clips.md` in
   the house style below: clips **chronological first, then a Ranking section**.
6. **Match the folder's existing clip files** (e.g. `memefi-stocks-clips.md`) for
   house style rather than guessing.
7. **Report** the clips + ranking, and flag any timestamp-precision limits.

## Selection — qualifies only if catchy AND worth posting
At least one of: hot take / contrarian claim · surprising stat or fact ·
relatable analogy · personal story or origin · memorable one-liner/hook · a clean
self-contained explanation of one important idea.

Quality guardrails: hook in the first ~3s (start on the strongest line, not
filler) · self-contained (makes sense with zero prior context) · **one idea per
clip** · start/end on natural sentence boundaries (never mid-sentence) · **end on
a punch** · skip filler, logistics, unresolved cross-talk.

## Length (hard rule)
Every clip **≥ 60s, never shorter.** Sweet spot 60–90s, up to ~2.5min if the
value justifies it. Always compute `end − start` and confirm ≥ 60s.

## House style (output format — every clip, every time)
```
Clip N : start–end  (≈Xs) — short tag

[Speaker]-led headline — the core point in plain words

"Full verbatim quote 1 pulled straight from the transcript"

"Full verbatim quote 2"
```
- **Speaker-led headline** ("Marcus on why Robinhood's capital is durable"), never
  a vague descriptor.
- **No quotation marks in headlines**, ever (not even around coined terms).
- **No ellipsis anywhere** — no `...`, no `(...)`. Never splice non-adjacent
  fragments; each quote is one **contiguous** stretch.
- **Every quote starts capitalized**; the rest stays **verbatim, word-for-word**
  (keep the transcript's real wording, including stutters/typos).
- **No `Caption:` / `Why it works:` lines. No emojis.**
- **Chronological clips first, then a Ranking section** ordered by
  viral / hot-take / controversy potential, with a short "Not shipped" note for
  anything dropped for length.

## Timestamps & precision
Block-level transcripts timestamp only every ~15–30s (block starts), so the true
cut usually falls *between* markers. Don't present an interpolated end as exact
(use `~07:15`). For each boundary give a `Cut:` line with the **in-words** and
**out-words** to scrub to, plus the real markers that bracket it. For frame-exact
cuts, require an `.srt`/word-level transcript or the media file.

## Rules
- Keep quotes verbatim; put transcription fixes (e.g. "board" → "borrowed
  conviction", "mean" → "meme stocks") in a bracketed note **outside** the quote.
- Free transcribers cut off (UniScribe free ≈ first 30 min) — say what couldn't be
  clipped past the cutoff rather than inventing timestamps.
- Confirm a guessed host name with the user before locking it into headlines.
- The standing source of truth is `~/Desktop/Clippings/rules.md`; keep this skill
  and that file in sync. Background: `domains/clippers/notes/`.
