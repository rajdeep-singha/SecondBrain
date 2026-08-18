#!/usr/bin/env python3
"""Embed notes into the local vector DB (.brain/index.db).

Incremental: a note is only re-embedded when its content hash changes; notes
removed from disk have their chunks dropped. Run after adding/editing notes:

    python scripts/embed.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import store  # noqa: E402


def main() -> int:
    db = store.connect()

    on_disk = {n.rel_path: n for n in common.iter_notes()}
    known = dict(db.execute("SELECT path, hash FROM files").fetchall())

    # Remove notes deleted from disk.
    removed = [p for p in known if p not in on_disk]
    for path in removed:
        _delete_note(db, path)

    changed = 0
    for rel_path, note in on_disk.items():
        h = common.content_hash(note.body)
        if known.get(rel_path) == h:
            continue
        _delete_note(db, rel_path)  # replace stale chunks (no-op if new)
        _insert_note(db, note, h)
        changed += 1

    db.commit()
    total_chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    db.close()

    print(f"embedded: {changed} changed, {len(removed)} removed, "
          f"{len(on_disk)} notes total, {total_chunks} chunks in index")
    if changed == 0 and not removed:
        print("index already up to date.")
    return 0


def _delete_note(db, path: str) -> None:
    ids = [r[0] for r in db.execute(
        "SELECT id FROM chunks WHERE path = ?", (path,)).fetchall()]
    for cid in ids:
        db.execute("DELETE FROM vec_chunks WHERE rowid = ?", (cid,))
    db.execute("DELETE FROM chunks WHERE path = ?", (path,))
    db.execute("DELETE FROM files WHERE path = ?", (path,))


def _insert_note(db, note: common.Note, h: str) -> None:
    chunks = store.chunk_note(note)
    vectors = store.embed_texts([text for _, text in chunks])
    tags = ",".join(note.tags)
    for (heading, text), vec in zip(chunks, vectors):
        cur = db.execute(
            "INSERT INTO chunks (path, domain, title, tags, heading, text) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (note.rel_path, note.domain, note.title, tags, heading, text),
        )
        db.execute(
            "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
            (cur.lastrowid, store.serialize(vec)),
        )
    db.execute(
        "INSERT OR REPLACE INTO files (path, hash) VALUES (?, ?)",
        (note.rel_path, h),
    )


if __name__ == "__main__":
    raise SystemExit(main())
