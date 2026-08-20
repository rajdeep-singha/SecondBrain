---
title: Fork → upstream PR workflow with gh
domain: general
tags: [git, github, gh-cli, fork, pull-request]
source: session
date: 2026-08-19
---

## Problem
Working in a **forked** repo (`origin` = your fork), you fixed a bug and want to
raise a PR against the original upstream repo — and optionally file a tracking
issue and keep a local notes file out of the push.

## Solution / code
```bash
# 1. branch off the base, commit only the fix files
git switch -c fix/my-change master
git add path/a path/b && git commit -m "fix: ..."

# 2. push to your fork
git push -u origin fix/my-change

# 3. open the PR against upstream (head is user:branch)
gh pr create \
  --repo Owner/repo \
  --base master \
  --head yourname:fix/my-change \
  --title "fix: ..." \
  --body "$(cat <<'EOF'
## What does this PR do?
...
Fixes #<issue-number>
EOF
)"
```

## Gotchas
- Issues can be **disabled on your fork** but enabled on upstream — `gh issue
  list`/`create` must target `--repo Owner/repo` (the original), not the fork.
- Link an issue with `Fixes #N` / `Closes #N` in the PR body so it auto-closes on
  merge into upstream.
- A forked fresh clone often has **no `upstream` remote**; confirm the parent with
  `gh repo view --json parent`. Pulling `upstream/master` can surface conflicts
  your local `master` doesn't have yet.
- Keep a local-only notes file unpushed: leave it untracked and stage files
  explicitly (never `git add .`), or add it to `.git/info/exclude`.
- Merge conflicts where one side changed a function **signature** (e.g. adding a
  `ctx context.Context` param / making it a method): "Accept current/incoming/both"
  are all wrong — both hunks are needed, and the call sites must change too. Resolve
  by hand, then `go build`.
