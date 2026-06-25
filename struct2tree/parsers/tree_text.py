"""Parser for directory-tree text (``tree`` command output or indented text).

Two formats, auto-detected:
- Format A: ``tree`` command ASCII box-drawing output (├── └── │).
- Format B: plain indented text (delegates to :mod:`text`).
"""

from __future__ import annotations

from ..models import Tree, TreeNode
from ..utils import get_content
from . import text as text_parser

BOX_CHARS = set("├└│─")


def _looks_like_box_art(content: str) -> bool:
    return any(ch in content for ch in ("├", "└", "│"))


def _box_depth_and_label(line: str) -> tuple[int, str]:
    """Compute nesting depth and label from a box-drawing tree line.

    The prefix is built from 4-char-wide segments: ``│   ``, ``    ``,
    ``├── ``, ``└── ``. Depth = number of leading segments before the
    connector (``├──``/``└──``). The label follows the connector.
    """
    # Find the connector position.
    idx = -1
    for marker in ("├── ", "└── ", "├──", "└──"):
        pos = line.find(marker)
        if pos != -1:
            idx = pos
            label = line[pos + len(marker.rstrip()) :].lstrip()
            # depth from the prefix width (segments of width 4)
            depth = pos // 4 + 1
            return depth, label.strip()
    # No connector -> top-level root line.
    return 0, line.strip()


def parse_tree_text(content: str, name: str | None = None) -> Tree:
    """Parse box-art or indented tree text into a :class:`Tree`."""
    if not _looks_like_box_art(content):
        return text_parser.parse_text(content, name=name)

    roots: list[TreeNode] = []
    stack: list[tuple[int, TreeNode]] = []

    for raw in content.splitlines():
        if not raw.strip():
            continue
        depth, label = _box_depth_and_label(raw)
        if not label:
            continue
        # Normalize directory markers: trailing slash means directory.
        node = TreeNode(label=label)

        while stack and stack[-1][0] >= depth:
            stack.pop()

        if not stack:
            roots.append(node)
        else:
            stack[-1][1].children.append(node)
        stack.append((depth, node))

    if name is None:
        name = roots[0].label if len(roots) == 1 else "tree"

    return Tree(name=name, roots=roots)


def parse(source: str, options: dict) -> Tree:
    """Parse tree-text from a file path or stdin content."""
    content = get_content(source, options)
    return parse_tree_text(content, name=options.get("name"))
