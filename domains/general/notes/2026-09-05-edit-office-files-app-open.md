---
title: Editing .xlsx/.numbers on disk while the app is open silently loses edits
domain: general
tags: [xlsx, numbers, openpyxl, numbers-parser, macos]
source: session
date: 2026-09-05
---

## Problem
Programmatic edits to a spreadsheet "didn't show up" and appeared to revert.
The edits *were* correctly written to disk every time — but Excel / Numbers /
Google Sheets had the file open, held its own in-memory copy, and never reloaded
from disk. Worse, the app's autosave (especially Numbers on quit) writes its
stale copy back over the on-disk edits.

## Solution / code
Close the file in the app **before** editing, and reopen fresh afterward.

`.numbers` isn't a zip openpyxl can touch — use `numbers-parser` in an isolated
venv so you don't touch system Python:

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install numbers-parser
```

Confirm nothing has the file open before writing:

```bash
lsof "StellarPay (Product Review).numbers"   # any output = app has it open
```

## Gotchas
- The disk write succeeding is **not** proof the user will see it — an open app
  masks it entirely. Re-reading the file in code confirms disk, not the UI.
- Numbers autosaves its cached copy on normal quit, clobbering your edits — close
  the doc *without saving* first, then re-apply if needed.
- Only edit **empty** target cells / leave user-corrected cells alone when told;
  a wrong-cell paste is hard to spot once the app re-caches.
