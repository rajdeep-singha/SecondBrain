"""Vector store + embedding helpers shared by embed.py and search.py.

Requires: fastembed, sqlite-vec  (see requirements.txt). Kept out of
build_index.py so the catalog stays dependency-free.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

DB_PATH = os.path.join(common.BRAIN_DIR, "index.db")
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

# Rough character budgets for chunking (chars ≈ tokens * 4).
MAX_CHUNK_CHARS = 2000  # ~500 tokens
OVERLAP_CHARS = 200


# ---------------------------------------------------------------- embeddings
@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding  # imported lazily; heavy

    return TextEmbedding(model_name=EMBED_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts -> list of float lists (EMBED_DIM each)."""
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]


# ------------------------------------------------------------------- chunking
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def chunk_note(note: common.Note) -> list[tuple[str, str]]:
    """Split a note body into (heading, text) chunks.

    Markdown-aware: sections are delimited by headings; oversized sections are
    windowed with overlap. The note title is prepended to every chunk so a
    chunk carries enough context to be retrieved on its own.
    """
    sections: list[tuple[str, list[str]]] = []
    current_heading = note.title
    current_lines: list[str] = []
    for line in note.body.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))

    chunks: list[tuple[str, str]] = []
    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if not text:
            continue
        prefix = f"{note.title} — {heading}\n"
        for window in _window(text):
            chunks.append((heading, prefix + window))
    if not chunks:  # note with only headings / empty body
        chunks.append((note.title, note.title))
    return chunks


def _window(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = start + MAX_CHUNK_CHARS
        out.append(text[start:end])
        if end >= len(text):
            break
        start = end - OVERLAP_CHARS
    return out


# ---------------------------------------------------------------------- store
def connect() -> sqlite3.Connection:
    import sqlite_vec  # lazy

    os.makedirs(common.BRAIN_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    _ensure_schema(db)
    return db


def _ensure_schema(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, hash TEXT)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS chunks ("
        " id INTEGER PRIMARY KEY,"
        " path TEXT, domain TEXT, title TEXT, tags TEXT, heading TEXT, text TEXT)"
    )
    db.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks "
        f"USING vec0(embedding float[{EMBED_DIM}])"
    )
    db.commit()


def serialize(vec: list[float]) -> bytes:
    import sqlite_vec

    return sqlite_vec.serialize_float32(vec)
