"""Format auto-detection: by file extension, and by content for stdin."""

from __future__ import annotations

import os

EXT_MAP = {
    ".xmind": "xmind",
    ".md": "markdown",
    ".markdown": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".txt": "text",
}


def detect_by_extension(path: str) -> str | None:
    """Return a format name from the file extension, or None if unknown."""
    ext = os.path.splitext(path)[1].lower()
    return EXT_MAP.get(ext)


def detect_by_content(content: str) -> str:
    """Heuristically detect format from raw text (for stdin).

    Order: JSON (starts with { or [) -> tree-text (box chars) -> markdown
    (list markers) -> yaml (key: + indentation) -> text fallback.
    """
    stripped = content.lstrip()
    if not stripped:
        return "text"

    # JSON: starts with { or [
    if stripped[0] in "{[":
        import json

        try:
            json.loads(content)
            return "json"
        except ValueError:
            pass  # looks like JSON but isn't valid; keep checking

    # tree-text: box-drawing characters
    if any(ch in content for ch in ("├", "└", "│")):
        return "tree-text"

    lines = [l for l in content.splitlines() if l.strip()]

    # markdown: a line whose first non-space chars are a list marker
    import re

    list_re = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
    if any(list_re.match(l) for l in lines):
        return "markdown"

    # yaml: lines like "key:" with indentation structure
    yaml_re = re.compile(r"^\s*[^:\s][^:]*:\s*(\S.*)?$")
    if sum(1 for l in lines if yaml_re.match(l)) >= max(1, len(lines) // 2):
        return "yaml"

    return "text"
