---
title: Clip selection + the hard ≥60s length rule
domain: clippers
tags: [clipping, video, hooks, workflow, touchgrass]
source: session
date: 2026-09-05
---

## Problem
Cutting clips from a long podcast/show transcript, I needed a repeatable bar for
*which* segments are worth posting and *how long* they must run — so an agent
produces post-ready clips every time without being re-briefed.

## Solution / code
Two standing rules, verified before finalizing each clip:

**Length (hard):** every clip **≥ 60s, never shorter**. Sweet spot 60–90s, up to
~2.5min if the value justifies it. Literally compute `end − start ≥ 60s`; if
under, extend to the nearest natural sentence boundary.

**Qualifies only if catchy AND worth posting** — needs at least one of:
- hot take / contrarian claim
- surprising stat or fact
- relatable analogy ("blockchains are cities")
- personal story / origin
- memorable one-liner / hook
- a clean self-contained explanation of one important idea

**Quality guardrails:** hook in first ~3s (start on the strongest line, not
"yeah, so, um…"); self-contained (makes sense with zero prior context); **one
idea per clip**; start/end on natural sentence boundaries (never mid-sentence);
**end on a punch**; skip filler/logistics/unresolved cross-talk.

## Gotchas
- The ≥60s floor kills genuinely viral-but-short segments (a ~47s Fartcoin riff).
  Don't silently drop them — log a "Not shipped" note so nothing viral is lost;
  if a full/paid transcript exists there's often adjacent audio to extend it.
- "Trim to the interesting core" beats shipping a long monologue with no hook.
- Deliver in [[clip-house-style-format]]; watch [[transcript-speaker-attribution]]
  and [[transcript-timestamp-precision-canva]].
