"""Internal data models shared by all parsers and the converter.

All parsers produce a :class:`Tree`; the converter consumes only this model.
Node ids are intentionally *not* stored on nodes — they are assigned by the
converter at output time from each node's position in the tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TreeNode:
    """A single node in the hierarchy.

    ``id`` is not stored here; the converter assigns it during serialization
    based on the node's path within :class:`Tree.roots`.
    """

    label: str
    children: list["TreeNode"] = field(default_factory=list)
    meta: dict[str, str] | None = None


@dataclass
class TreeRef:
    """A cross-node relationship (a graph edge outside the tree nesting).

    Paths are 0-indexed lists of child positions. ``[0, 1]`` means the second
    child of the first root. The converter maps these paths to ``1.2``-style ids.
    """

    from_path: list[int]
    to_path: list[int]
    rel: str
    note: str | None = None


@dataclass
class Tree:
    """A complete parsed structure: a title, one or more roots, and refs."""

    name: str
    roots: list[TreeNode] = field(default_factory=list)
    refs: list[TreeRef] = field(default_factory=list)
