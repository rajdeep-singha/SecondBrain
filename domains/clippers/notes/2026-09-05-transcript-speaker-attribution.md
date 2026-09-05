---
title: Attribute clip quotes by content — transcript speaker labels lie
domain: clippers
tags: [clipping, transcription, attribution, touchgrass, solana]
source: session
date: 2026-09-05
---

## Problem
Auto-transcripts (UniScribe etc.) label speakers "Speaker 1/2/3", and the labels
are frequently **wrong or swapped** — e.g. a compliance answer that is clearly the
founder's got attributed to the interviewer. Trusting the labels puts the wrong
name on a clip headline.

## Solution / code
- **Attribute by content/context, not by the raw "Speaker N" label.** Read who is
  plausibly saying each line from the substance.
- **The host/guest cast changes every episode — never assume a fixed set of
  names.** Figure out who's who from the transcript intro (it usually names the
  show + guest), or wait for the user to tell you. A solo monologue (e.g. a
  single-host news show) attributes everything to that one host.
- Don't carry a previous episode's cast into a new folder/episode.

## Gotchas
- Even the *words* can be mis-transcribed: "board conviction" was really "borrowed
  conviction"; "mean stocks" was "meme stocks". Keep the quote verbatim per
  [[clip-house-style-format]] but flag the fix in a bracketed note *outside* the
  quote so the caption reads right.
- Confirm a guessed host name with the user before locking it into every headline.
- Feeds [[clip-house-style-format]] and [[clip-selection-and-length-guardrails]].
