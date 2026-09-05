---
title: Split shared files into per-feature commits with cached patches
domain: general
tags: [git, staging, patch, commits, workflow]
source: session
date: 2026-09-05
---

## Problem
You want one commit per feature, but several files (`types.ts`, config, `app.ts`)
are touched by *multiple* features. Whole-file `git add` can't split them, and a
messy history hurts review.

## Solution / code
Whole-file `git add` the files that belong to a single feature; for shared files,
carve out the feature's hunks into a patch and stage it with `git apply --cached`:

```bash
git reset -q                     # clean staging slate, files untouched
# feature-only files:
git add server/src/controllers/project-token.controllers.ts
# feature-only hunks of a shared file:
git apply --cached .split-patches/c1-types.patch
git commit -m "feat(server): project_token integration"
```

Verify every patch applies and dry-run the full staging sequence (stage, then
`git reset`) before making any real commit.

## Gotchas
- Keep each commit **build-clean**: put the route/import wiring (`app.ts`) that
  references a new module in the *later* commit that also adds the caller, so an
  earlier commit doesn't import something not yet used.
- A single hunk can mix two features' additions — you then have to sub-split the
  hunk by hand-editing the patch file.
- Hand-authored patches must keep exact `@@` line ranges and context or
  `git apply` rejects them — generate from a real `git diff`, don't retype.
- To land the result on an already-pushed branch, amend + `git push
  --force-with-lease` (rewrites history) — see [[fork-pr-upstream-workflow]] and
  [[gofmt-ci-format-gate]].
