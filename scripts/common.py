"""Shared utilities for the SecondBrain pipeline.

Stdlib only — no third-party deps here so that build_index.py stays dependency
free (embed.py / search.py add fastembed + sqlite-vec on top of this).
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Iterator

# Repo root = parent of the scripts/ directory this file lives in.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS_DIR = os.path.join(ROOT, "domains")
TWEETS_DIR = os.path.join(ROOT, "tweets")
SKILLS_DIR = os.path.join(ROOT, "skills")
BRAIN_DIR = os.path.join(ROOT, ".brain")

REQUIRED_KEYS = ("title", "domain", "source")
VALID_SOURCES = ("session", "tweet", "manual")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


@dataclass
class Note:
    path: str  # absolute path
    rel_path: str  # path relative to repo root (stable id)
    domain: str
    meta: dict
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or os.path.basename(self.path))

    @property
    def tags(self) -> list[str]:
        return _as_list(self.meta.get("tags"))

    @property
    def source(self) -> str:
        return str(self.meta.get("source") or "")

    @property
    def date(self) -> str:
        return str(self.meta.get("date") or "")


def _as_list(value) -> list[str]:
    """Coerce a frontmatter value into a list of strings.

    Accepts YAML flow lists ([a, b]) and comma-separated scalars.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return [p.strip().strip("'\"") for p in text.split(",") if p.strip()]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a minimal YAML frontmatter block.

    Supports the small subset we actually use: `key: scalar` and
    `key: [a, b, c]`. Returns (meta, body). No PyYAML dependency.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw, body = match.group(1), match.group(2)
    meta: dict = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = _as_list(value)
        else:
            meta[key] = value.strip("'\"")
    return meta, body


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_note(path: str) -> Note:
    text = _read(path)
    meta, body = parse_frontmatter(text)
    rel = os.path.relpath(path, ROOT)
    domain = str(meta.get("domain") or _infer_domain(rel))
    note = Note(path=path, rel_path=rel, domain=domain, meta=meta, body=body)
    note.errors = validate(note)
    return note


def _infer_domain(rel_path: str) -> str:
    parts = rel_path.split(os.sep)
    if parts and parts[0] == "domains" and len(parts) > 1:
        return parts[1]
    if parts and parts[0] == "tweets":
        return "tweets"
    return ""


def valid_domains() -> set[str]:
    domains = set()
    if os.path.isdir(DOMAINS_DIR):
        domains.update(
            d for d in os.listdir(DOMAINS_DIR)
            if os.path.isdir(os.path.join(DOMAINS_DIR, d))
        )
    domains.add("tweets")
    return domains


def validate(note: Note) -> list[str]:
    errors = []
    for key in REQUIRED_KEYS:
        if not note.meta.get(key):
            errors.append(f"missing required frontmatter '{key}'")
    if note.domain and note.domain not in valid_domains():
        errors.append(f"unknown domain '{note.domain}'")
    src = note.meta.get("source")
    if src and src not in VALID_SOURCES:
        errors.append(f"invalid source '{src}' (expected one of {VALID_SOURCES})")
    return errors


def iter_note_paths() -> Iterator[str]:
    """Yield every knowledge note: domains/*/notes/*.md and tweets/*.md."""
    if os.path.isdir(DOMAINS_DIR):
        for domain in sorted(os.listdir(DOMAINS_DIR)):
            notes_dir = os.path.join(DOMAINS_DIR, domain, "notes")
            if not os.path.isdir(notes_dir):
                continue
            for name in sorted(os.listdir(notes_dir)):
                if name.endswith(".md") and not name.startswith("."):
                    yield os.path.join(notes_dir, name)
    if os.path.isdir(TWEETS_DIR):
        for name in sorted(os.listdir(TWEETS_DIR)):
            if name.endswith(".md") and not name.startswith("."):
                yield os.path.join(TWEETS_DIR, name)


def iter_notes() -> Iterator[Note]:
    for path in iter_note_paths():
        yield load_note(path)


def first_sentence(body: str, limit: int = 180) -> str:
    """First meaningful sentence of a note body, for the catalog table."""
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        # Stop at the first sentence terminator, else truncate.
        m = re.search(r"[.!?](\s|$)", line)
        snippet = line[: m.start() + 1] if m else line
        if len(snippet) > limit:
            snippet = snippet[: limit - 1].rstrip() + "…"
        return snippet.replace("|", "\\|")  # keep markdown tables intact
    return ""


def iter_skills() -> Iterator[dict]:
    """Yield {name, description, dir} for each skills/*/SKILL.md."""
    if not os.path.isdir(SKILLS_DIR):
        return
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        meta, _ = parse_frontmatter(_read(skill_md))
        yield {
            "dir": name,
            "name": str(meta.get("name") or name),
            "description": str(meta.get("description") or ""),
        }
