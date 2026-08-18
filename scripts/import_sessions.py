#!/usr/bin/env python3
"""Harvest new Claude Code sessions from allow-listed folders into the inbox.

Claude Code logs every session, in every folder, to
`~/.claude/projects/<encoded-path>/<session-id>.jsonl`. This script scans those
logs, keeps only sessions whose working-directory basename matches a pattern in
`import.allowlist`, and drops each NEW session as a raw markdown file into
`sessions/inbox/` for the `distill-session` skill to process.

On-demand and idempotent: already-imported sessions (tracked in
`.brain/imported.json`) are skipped, so re-running only pulls what's new.

    python scripts/import_sessions.py          # import new sessions
    python scripts/import_sessions.py --dry-run # list what would be imported
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
INBOX_DIR = os.path.join(common.ROOT, "sessions", "inbox")
ALLOWLIST_FILE = os.path.join(common.ROOT, "import.allowlist")
STATE_FILE = os.path.join(common.BRAIN_DIR, "imported.json")

MAX_CHARS = 40_000  # cap a single raw dump; distillation extracts the signal
MIN_USER_CHARS = 40  # skip trivial/empty sessions


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="list importable sessions without writing files")
    args = ap.parse_args()

    if not os.path.isdir(PROJECTS_DIR):
        print(f"no Claude projects dir at {PROJECTS_DIR}", file=sys.stderr)
        return 1

    patterns = load_allowlist()
    if not patterns:
        print("import.allowlist is empty — nothing to harvest.", file=sys.stderr)
        return 1
    state = load_state()
    seen = state["sessions"]

    imported = skipped_seen = skipped_scope = 0
    os.makedirs(INBOX_DIR, exist_ok=True)

    for jsonl in iter_transcripts():
        session = parse_transcript(jsonl)
        if session is None:
            continue
        basename = os.path.basename(session["cwd"].rstrip("/")) or "unknown"
        if not matches(basename, patterns):
            skipped_scope += 1
            continue
        if session["session_id"] in seen:
            skipped_seen += 1
            continue
        if len(session["user_chars"]) < MIN_USER_CHARS:
            continue

        fname = f"{_slug(basename)}-{session['date']}-{session['session_id'][:8]}.md"
        dest = os.path.join(INBOX_DIR, fname)
        if args.dry_run:
            print(f"WOULD import  {basename:24s} {session['date']}  -> {fname}")
        else:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(render(session, basename))
            seen[session["session_id"]] = {
                "file": fname,
                "folder": basename,
                "src": os.path.relpath(jsonl, os.path.expanduser("~")),
                "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            print(f"imported  {basename:24s} {session['date']}  -> sessions/inbox/{fname}")
        imported += 1

    if not args.dry_run:
        save_state(state)

    verb = "importable" if args.dry_run else "imported"
    print(f"\n{imported} {verb}, {skipped_seen} already seen, "
          f"{skipped_scope} out of scope.")
    if imported and not args.dry_run:
        print("next: run the `distill-session` skill on sessions/inbox/, then `make index`.")
    return 0


# --------------------------------------------------------------- allowlist
def load_allowlist() -> list[str]:
    if not os.path.exists(ALLOWLIST_FILE):
        return []
    out = []
    for line in open(ALLOWLIST_FILE, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def matches(basename: str, patterns: list[str]) -> bool:
    low = basename.lower()
    return any(fnmatch.fnmatch(low, p.lower()) for p in patterns)


# ------------------------------------------------------------------- state
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
            data.setdefault("sessions", {})
            return data
    return {"sessions": {}}


def save_state(state: dict) -> None:
    os.makedirs(common.BRAIN_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


# -------------------------------------------------------------- transcripts
def iter_transcripts():
    for entry in sorted(os.listdir(PROJECTS_DIR)):
        proj = os.path.join(PROJECTS_DIR, entry)
        if not os.path.isdir(proj):
            continue
        for name in sorted(os.listdir(proj)):
            if name.endswith(".jsonl"):
                yield os.path.join(proj, name)


def parse_transcript(path: str):
    """Extract a readable conversation from a transcript .jsonl.

    Returns dict(session_id, cwd, date, turns[list[(role,text)]], user_chars)
    or None if there's no usable conversation.
    """
    session_id = os.path.splitext(os.path.basename(path))[0]
    cwd = ""
    date = ""
    turns: list[tuple[str, str]] = []
    user_chars: list[str] = []

    for line in _read_lines(path):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("cwd") and not cwd:
            cwd = obj["cwd"]
        if obj.get("sessionId"):
            session_id = obj["sessionId"]
        ts = obj.get("timestamp")
        if ts and not date:
            date = ts[:10]

        t = obj.get("type")
        if t not in ("user", "assistant"):
            continue
        text = _extract_text(obj.get("message", {}), role=t)
        if not text:
            continue
        turns.append(("me" if t == "user" else "claude", text))
        if t == "user":
            user_chars.append(text)

    if not turns or not cwd:
        return None
    return {
        "session_id": session_id,
        "cwd": cwd,
        "date": date or "unknown",
        "turns": turns,
        "user_chars": "".join(user_chars),
    }


def _extract_text(message: dict, role: str) -> str:
    """Pull human-readable text; drop thinking, tool_use, and tool_result noise."""
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        # Skip command/system wrappers and tool-result echoes.
        if text.startswith("<") and text.endswith(">"):
            return ""
        return text
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")).strip())
        return "\n\n".join(p for p in parts if p)
    return ""


def _read_lines(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        yield from fh


# ------------------------------------------------------------------ render
def render(session: dict, basename: str) -> str:
    header = [
        f"# raw session import — {basename}",
        "",
        f"- folder: `{session['cwd']}`",
        f"- session: `{session['session_id']}`",
        f"- date: {session['date']}",
        "",
        "> Unprocessed export. Run the `distill-session` skill to file the reusable",
        "> lessons as notes, then move this file to `sessions/processed/`.",
        "",
        "---",
        "",
    ]
    body_parts, total = [], 0
    truncated = False
    for role, text in session["turns"]:
        chunk = f"**{role}:** {text}\n"
        if total + len(chunk) > MAX_CHARS:
            truncated = True
            break
        body_parts.append(chunk)
        total += len(chunk)
    if truncated:
        body_parts.append("\n_[truncated — session longer than import cap]_\n")
    return "\n".join(header) + "\n".join(body_parts)


def _slug(text: str) -> str:
    keep = "".join(c if c.isalnum() or c in "-_" else "-" for c in text)
    return keep.strip("-").lower() or "session"


if __name__ == "__main__":
    raise SystemExit(main())
