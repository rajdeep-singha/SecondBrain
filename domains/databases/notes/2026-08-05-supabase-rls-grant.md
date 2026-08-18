---
title: Supabase anon inserts need a table GRANT, not just an RLS policy
domain: databases
tags: [supabase, postgres, rls, permissions, security]
source: session
date: 2026-08-05
---

## Problem
A Supabase table has RLS enabled and an INSERT policy for `anon`, but the
frontend form still fails with Postgres error `42501: permission denied`.

## Solution / code
RLS policies and table privileges are **two separate layers**. A policy only
controls *which rows* a role may touch; the role also needs the table-level
`GRANT`. Tables created via the raw **SQL editor** don't always inherit the
default grants (tables made via the dashboard Table Editor do). Add:

```sql
grant insert on public.job_applications to anon, authenticated;
```

Run just that one statement (re-running the whole setup file errors with
`42710: policy ... already exists`).

## Gotchas
- `42501` (permission denied) = missing GRANT; `42710` = policy already exists
  (you re-ran the create-policy statement). They're different failures.
- The `anon` key is **public** (it ships in the frontend bundle). Ensure the table
  has **no SELECT policy**, or anyone can read all rows. Omit SELECT so reads are
  blocked; view data via the Table Editor.
- Rule of thumb: enabling RLS + adding a policy is not enough — verify the base
  `GRANT` for the role too.
