#!/usr/bin/env python3
"""Semantic search over the SecondBrain vector DB.

    python scripts/search.py "how did I do an aptos coin transfer?"
    python scripts/search.py "agent memory" --domain ai-agents -k 3
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Semantic search over notes.")
    ap.add_argument("query", help="natural-language query")
    ap.add_argument("--domain", "-d", help="restrict to one domain")
    ap.add_argument("-k", type=int, default=5, help="number of results")
    args = ap.parse_args()

    if not os.path.exists(store.DB_PATH):
        print("no index found — run `python scripts/embed.py` first.", file=sys.stderr)
        return 1

    db = store.connect()
    qvec = store.serialize(store.embed_one(args.query))

    # Over-fetch so an optional domain filter still returns k results.
    fetch = args.k * 6 if args.domain else args.k
    rows = db.execute(
        "SELECT c.path, c.domain, c.heading, c.text, v.distance "
        "FROM vec_chunks v JOIN chunks c ON c.id = v.rowid "
        "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
        (qvec, fetch),
    ).fetchall()
    db.close()

    if args.domain:
        rows = [r for r in rows if r[1] == args.domain]
    rows = rows[: args.k]

    if not rows:
        print("no matches.")
        return 0

    for i, (path, domain, heading, text, distance) in enumerate(rows, 1):
        score = 1.0 / (1.0 + distance)  # map L2 distance -> (0,1] for readability
        print(f"\n[{i}] {domain}  ·  score={score:.3f}")
        print(f"    {path}  ({heading})")
        print(f"    {_snippet(text)}")
    return 0


def _snippet(text: str, limit: int = 240) -> str:
    # Drop the "title — heading" context prefix we added at embed time.
    body = text.split("\n", 1)[1] if "\n" in text else text
    body = " ".join(body.split())
    return body[:limit] + ("…" if len(body) > limit else "")


if __name__ == "__main__":
    raise SystemExit(main())
