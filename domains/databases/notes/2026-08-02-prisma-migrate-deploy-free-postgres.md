---
title: Prisma auto-migrate on deploy + surviving free-tier Postgres expiry
domain: databases
tags: [prisma, postgres, render, railway, neon, deployment, migrations]
source: session
date: 2026-08-02
---

## Problem
A free-tier Postgres (Render/Railway) gets deleted after ~30 days, taking the
schema with it. How to recreate the DB with minimal manual work.

## Solution / code
If the deploy command already runs `prisma migrate deploy` on startup, the schema
**rebuilds itself** — you only need a fresh Postgres and a correct `DATABASE_URL`:

```
# nixpacks.toml / Dockerfile start command
npx prisma migrate deploy && node dist/index.js
```

Recreate steps: create new Postgres → copy its connection URL → update the
backend service's `DATABASE_URL` env var → the redeploy runs migrations and
recreates all tables. Optional: `DATABASE_URL="<external-url>" npm run seed`, and
inspect with `npx prisma studio`.

Use the **Internal** DB URL when app + DB are in the same region (faster, no
egress); use the **External** URL for running migrations/seed from your laptop.

## Gotchas
- Free-tier Postgres on Render/Railway **expires and is deleted (~30 days)** — the
  recurring pain. To stop redoing this monthly, use a non-expiring free tier:
  **Neon** or **Supabase**.
- Don't paste live DB credentials into a chat — run seed/verify steps yourself.
- Put the DB in the **same region** as the backend before choosing the internal URL.
