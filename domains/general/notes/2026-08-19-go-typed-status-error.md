---
title: Carry HTTP status in a typed Go error, detect via errors.As
domain: general
tags: [go, errors, errors-as, http, proxy]
source: session
date: 2026-08-19
---

## Problem
Code inferred "was this request blocked?" from the result struct:

```go
isBlocked := result != nil && result.StatusCode == 403
```

But the handlers `return nil, err` on any 4xx — so `result` is `nil` exactly
when a 403 happens. `isBlocked` was **always false**, so the whole
block-detection / proxy-cooldown path was dead code.

## Solution / code
Don't smuggle status through a nil-able result. Carry it in a **typed error** and
detect it with `errors.As`, which unwraps `%w`-wrapped chains:

```go
type StatusError struct {
	Handler    string
	StatusCode int
}
func (e *StatusError) Error() string  { /* keep the numeric code in the msg */ }

func IsBlockedStatus(code int) bool { return code == 403 || code == 429 }

func IsBlockedErr(err error) bool {
	var se *StatusError
	return errors.As(err, &se) && IsBlockedStatus(se.StatusCode)
}
```

Handlers return `&StatusError{...}` on `>= 400`; the caller then does:

```go
isBlocked := IsBlockedErr(lastErr) || (result != nil && IsBlockedStatus(result.StatusCode))
```

## Gotchas
- `errors.As` only unwraps if every layer wraps with `%w` (`fmt.Errorf("...: %w",
  err)`), not `%v`.
- Keep the numeric code in `Error()` if other code (log hints, string matches)
  greps the message for "403".
- Treat 429 as "blocked" alongside 403 — same "this IP is being rejected" signal
  that should trigger a cooldown.
- Watch for handlers that hardcode a status (e.g. browser handler returning
  `StatusCode: 200`); they silently bypass the detection and are a separate call.
