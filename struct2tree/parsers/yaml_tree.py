"""Minimal YAML parser (``.yaml`` / ``.yml``) — standard library only.

Supports the subset needed for hierarchical structures: nested mappings,
scalar leaves, and sequences. Anchors, aliases, flow collections, and
multi-line/block scalars are not supported — they trigger a warning and
best-effort handling.
"""

from __future__ import annotations

from ..models import Tree, TreeNode
from ..utils import get_content, warn


def _indent_width(line: str) -> int:
    width = 0
    for ch in line:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 2
        else:
            break
    return width


def _strip_comment(line: str) -> str:
    """Remove a trailing ``#`` comment that is not inside quotes."""
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1] in " \t":
                return line[:i]
    return line


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _warn_complex(line: str) -> None:
    stripped = line.strip()
    if stripped.startswith("&") or " &" in line:
        warn("YAML anchors are not supported; best-effort parse")
    if stripped.startswith("*") or " *" in line:
        warn("YAML aliases are not supported; best-effort parse")
    if "|" in stripped[:3] or ">" in stripped[:3]:
        warn("YAML block scalars are not supported; best-effort parse")


def _parse_lines(lines: list[str]) -> list[TreeNode]:
    """Parse a list of (already comment-stripped) YAML lines into roots."""
    roots: list[TreeNode] = []
    # stack of (indent, node)
    stack: list[tuple[int, TreeNode]] = []
    # pending sequence target: the node whose value is a sequence
    seq_owner: TreeNode | None = None

    for raw in lines:
        if not raw.strip():
            continue
        _warn_complex(raw)
        indent = _indent_width(raw)
        body = raw.strip()

        # Sequence item: "- value"
        if body.startswith("- "):
            item_val = _clean_scalar(body[2:])
            # attach to the nearest mapping node at lower indent
            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent = stack[-1][1] if stack else None
            child = TreeNode(label=item_val)
            if parent is not None:
                parent.children.append(child)
            else:
                roots.append(child)
            continue

        # Mapping entry: "key:" or "key: value"
        if ":" not in body:
            # bare scalar line — treat as a leaf node
            node = TreeNode(label=_clean_scalar(body))
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if stack:
                stack[-1][1].children.append(node)
            else:
                roots.append(node)
            stack.append((indent, node))
            continue

        key, _, val = body.partition(":")
        key = _clean_scalar(key)
        val = val.strip()
        node = TreeNode(label=key)

        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            stack[-1][1].children.append(node)
        else:
            roots.append(node)
        stack.append((indent, node))

        if val and val not in ("|", ">"):
            node.meta = {"value": _clean_scalar(val)}

    return roots


def parse(source: str, options: dict) -> Tree:
    content = get_content(source, options)
    name = options.get("name")

    lines = [_strip_comment(l) for l in content.splitlines()]
    # drop document markers
    lines = [l for l in lines if l.strip() not in ("---", "...")]

    roots = _parse_lines(lines)

    if name is None:
        name = roots[0].label if len(roots) == 1 else "tree"

    return Tree(name=name, roots=roots)
