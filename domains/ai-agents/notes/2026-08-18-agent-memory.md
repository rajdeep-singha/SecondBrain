---
title: Giving an AI agent persistent memory
domain: ai-agents
tags: [memory, rag, embeddings, retrieval]
source: session
date: 2026-08-18
---

## Problem
An LLM agent forgets everything between runs. It needs to recall past facts,
decisions, and learnings without stuffing the entire history into every prompt.

## Solution / code
Separate short-term (in-context) from long-term (retrieved) memory. Persist
long-term memory as small notes, embed them, and retrieve the top-k relevant
chunks by semantic similarity at query time — inject only those into the prompt.

```
write:  fact ── chunk ── embed ── upsert(vector, text, meta) ─▶ vector store
read:   query ── embed ── top_k(cosine) ── inject into prompt
```

Keep each memory atomic (one fact per note) with metadata (source, date, tags)
so retrieval stays precise and you can filter by domain.

## Gotchas
- Chunk on semantic boundaries (headings/paragraphs), not fixed byte windows, or
  retrieval quality drops.
- Deduplicate by content hash before embedding to avoid re-indexing unchanged notes.
- Local embedding models (ONNX/CPU) are usually enough at personal scale and
  avoid API keys and cost.
