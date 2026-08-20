---
title: Non-blocking load-shedding on a Go worker-pool channel
domain: general
tags: [go, concurrency, channels, backpressure, http]
source: session
date: 2026-08-19
---

## Problem
A worker pool submitted jobs with a bare channel send:

```go
func (p *Pool) Submit(msg JobMessage) { p.jobs <- msg } // "non-blocking if buffer has space"
```

When the buffered channel (`JOB_BUFFER_SIZE`) fills and all workers are busy, the
send **blocks the HTTP request goroutine** that called it. Clients hang with no
fast failure, no `Retry-After`, and request goroutines pile up holding
connections/memory. Worst for a sync endpoint that blocks *before* its own
polling/timeout logic even starts.

## Solution / code
Make `Submit` a non-blocking try-send returning a bool; shed load on a full
buffer (a full buffer is a genuine overload signal):

```go
func (p *Pool) Submit(msg JobMessage) bool {
	select {
	case p.jobs <- msg:
		return true
	default:
		return false // buffer full → caller sheds load
	}
}
```

Callers return **503 + `Retry-After`** when rejected.

## Gotchas
- If callers create the job row (status `pending`) **before** submitting, a
  rejected submit must mark that row `failed` — otherwise it's a permanent
  `pending` zombie the worker never picks up.
- For batch submits, mark the individual rejected child `failed` and continue
  (partial batch) rather than aborting the whole request.
- Test the contract with a buffer-of-1 pool and **no** workers draining: a second
  submit must return `false`, not hang. A regression to blocking makes the test
  time out instead of failing cleanly.
- Pure load-shedding vs. bounded wait (block up to the request deadline) is a real
  design choice; pure shed is simpler and the buffer already absorbs bursts.
