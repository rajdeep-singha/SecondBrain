---
title: gofmt CI format gate fails on double blank lines
domain: general
tags: [go, gofmt, ci, tooling]
source: session
date: 2026-08-19
---

## Problem
CI "Build/Test/Vet" all showed as failed, but the real failure was an earlier
**format gate** that the others were gated behind:

```bash
test -z "$(gofmt -l .)"
```

This fails (non-empty output) if *any* file isn't gofmt-clean. Build/Test never
ran. The offending change: **double blank lines** between functions, which gofmt
collapses to a single blank line.

## Solution / code
Run the same check locally before every push, and auto-fix:

```bash
cd server && gofmt -l .   # any output = needs formatting; empty = clean
gofmt -w .                # apply fixes in place
```

To land the format fix on an open PR branch, amend + force-push (safe variant):

```bash
git add path/to/file.go && git commit --amend --no-edit && git push --force-with-lease
```

## Gotchas
- Editors/linters can *re-introduce* the double blank line after you fix it —
  re-run `gofmt -l .` right before committing, not just once.
- `gofmt -d` exits **1** when it finds diffs, which short-circuits an `&&` chain
  before a following `-w` runs — run `-w` as its own command.
- `go test`/`go vet` from the repo root won't find the module if `go.mod` lives in
  a subdir (e.g. `server/`) — run from there.
