"""Markdown outline parser (``.md``).

Recognizes nested ordered/unordered list structure and converts it to a tree.
Optional extensions (off by default):
- ``--parse-meta``: ``{key:value, ...}`` trailing braces on a list item -> meta
- ``--parse-ref``:  a ``[ref]`` region whose lines describe cross-node edges
"""

from __future__ import annotations

import re

from ..models import Tree, TreeNode, TreeRef
from ..utils import get_content, warn

# - / * / + bullet, or "1." style ordered marker
_LIST_RE = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+(.*)$")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
_META_RE = re.compile(r"\s*\{([^}]*)\}\s*$")
_REF_LINE_RE = re.compile(
    r"^\[ref\]:\s*(.+?)\s*->\s*(.+?)\s*(?:\|\s*(.*?)\s*(?:\|\s*(.*?))?)?$"
)
_REF_HEADER_RE = re.compile(r"^(\[ref\]|<!--\s*ref\s*-->)", re.IGNORECASE)


def _indent_level(indent: str) -> int:
    """2 spaces or 1 tab per level."""
    width = 0
    for ch in indent:
        width += 2 if ch == "\t" else 1
    return width // 2


def _extract_meta(label: str) -> tuple[str, dict[str, str] | None]:
    """Pull a trailing ``{k:v, k:v}`` from a label, if present."""
    m = _META_RE.search(label)
    if not m:
        return label, None
    body = m.group(1)
    meta: dict[str, str] = {}
    for pair in body.split(","):
        if ":" not in pair:
            continue
        k, _, v = pair.partition(":")
        k, v = k.strip(), v.strip()
        if k:
            meta[k] = v
    clean = label[: m.start()].rstrip()
    return clean, (meta or None)


def _id_str_to_path(id_str: str) -> list[int]:
    """Convert a dotted 1-indexed id like ``1.2`` to a 0-indexed path."""
    return [int(p) - 1 for p in id_str.strip().split(".") if p.strip()]


def parse(source: str, options: dict) -> Tree:
    content = get_content(source, options)
    parse_meta = options.get("parse_meta", False)
    parse_ref = options.get("parse_ref", False)
    name = options.get("name")

    lines = content.splitlines()

    # Split off a trailing ref region if ref parsing is enabled.
    ref_lines: list[str] = []
    if parse_ref:
        ref_start = None
        for i, line in enumerate(lines):
            if _REF_HEADER_RE.match(line.strip()):
                ref_start = i
                break
        if ref_start is not None:
            ref_lines = lines[ref_start:]
            lines = lines[:ref_start]

    roots: list[TreeNode] = []
    stack: list[tuple[int, TreeNode]] = []
    heading_name: str | None = None
    seen_list = False

    for raw in lines:
        if not raw.strip():
            continue

        m = _LIST_RE.match(raw)
        if not m:
            # Non-list line: a heading before the list can become tree name.
            if not seen_list:
                h = _HEADING_RE.match(raw.strip())
                if h and heading_name is None:
                    heading_name = h.group(1).strip()
            else:
                warn(f"ignoring non-list line inside list: {raw.strip()!r}")
            continue

        seen_list = True
        level = _indent_level(m.group(1))
        label = m.group(2).strip()
        meta = None
        if parse_meta:
            label, meta = _extract_meta(label)

        node = TreeNode(label=label, meta=meta)

        while stack and stack[-1][0] >= level:
            stack.pop()
        if not stack:
            roots.append(node)
        else:
            stack[-1][1].children.append(node)
        stack.append((level, node))

    refs: list[TreeRef] = []
    for raw in ref_lines:
        line = raw.strip()
        rm = _REF_LINE_RE.match(line)
        if not rm:
            continue
        from_id, to_id, rel, note = rm.group(1), rm.group(2), rm.group(3), rm.group(4)
        refs.append(
            TreeRef(
                from_path=_id_str_to_path(from_id),
                to_path=_id_str_to_path(to_id),
                rel=(rel or "see-also").strip(),
                note=note.strip() if note else None,
            )
        )

    if name is None:
        name = heading_name or (roots[0].label if len(roots) == 1 else "tree")

    return Tree(name=name, roots=roots, refs=refs)
