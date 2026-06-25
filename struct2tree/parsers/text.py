"""Indented plain-text parser (``.txt``).

Each level of nesting is 2 spaces or 1 tab. The first line (if it is the sole
top-level node) becomes the tree name as well as a root node.
"""

from __future__ import annotations

from ..models import Tree, TreeNode
from ..utils import get_content


def _indent_width(line: str) -> int:
    """Return the indentation level of a line (2 spaces or 1 tab = 1 level)."""
    width = 0
    for ch in line:
        if ch == "\t":
            width += 2  # one tab counts as one level (= 2 spaces)
        elif ch == " ":
            width += 1
        else:
            break
    return width // 2


def parse_text(content: str, name: str | None = None) -> Tree:
    """Parse indented text into a :class:`Tree`. Shared by the text-text parser."""
    roots: list[TreeNode] = []
    # stack of (level, node); root level is 0
    stack: list[tuple[int, TreeNode]] = []

    for raw in content.splitlines():
        if not raw.strip():
            continue
        level = _indent_width(raw)
        label = raw.strip()
        node = TreeNode(label=label)

        # pop until the top of the stack is the parent (level-1)
        while stack and stack[-1][0] >= level:
            stack.pop()

        if not stack:
            roots.append(node)
        else:
            stack[-1][1].children.append(node)
        stack.append((level, node))

    if name is None:
        name = roots[0].label if len(roots) == 1 else "tree"

    return Tree(name=name, roots=roots)


def parse(source: str, options: dict) -> Tree:
    """Parse a ``.txt`` file path (or stdin content) into a :class:`Tree`."""
    content = get_content(source, options)
    return parse_text(content, name=options.get("name"))
