---
title: Block-level transcript timestamps can't give frame-accurate cuts for Canva
domain: clippers
tags: [clipping, canva, timestamps, srt, transcription, yahoo]
source: session
date: 2026-09-05
---

## Problem
Clipping in Canva needs precise start **and** end timestamps. Auto-transcripts
only carry a timestamp every ~15–30s (each marks the *start* of a spoken block),
so the true cut point usually falls **between** two markers. Interpolating end
times "by feel" produced stamps that were off — not good enough for a frame cut.

## Solution / code
Be honest about the limit and give scrubbing cues instead of fake precision:

For each clip boundary, provide a `Cut:` line with:
- the exact **in-words** and **out-words** to scrub to, and
- the **real transcript markers that bracket** the boundary, e.g.
  `OUT mid-block between 08:42 and 09:01, after "...actual stocks" — stop BEFORE
  "Now, the AMC CEO..."`.

That gets within a second or two by scrubbing in the editor.

For **true frame-accurate** stamps, ask up front for either the **video/audio
file** or a **word-level transcript** (`.srt` / `.vtt` with per-line timings) and
pin every start/end exactly.

## Gotchas
- Clip *starts* often sit on real markers; the *ends* are what get interpolated —
  don't present an interpolated end as an exact stamp (use `~07:15`, not `07:15`).
- Free transcription tools cut off (UniScribe free ≈ first 30 min; another stopped
  at ~52:20 "6 more minutes locked") — anything past the cutoff can't be clipped;
  say so rather than inventing timestamps.
- Ask for the .srt/word-level transcript *before* starting when the target is
  Canva. Pairs with [[clip-house-style-format]].
