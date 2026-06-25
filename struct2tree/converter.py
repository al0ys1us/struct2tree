"""Core converter: internal :class:`Tree` model -> XML output string.

Responsibilities:
- Assign hierarchical ids (``1``, ``1.1``, ``1.2.3`` ...) from node positions.
- Map :class:`TreeRef` 0-indexed paths to those ids.
- Serialize with 2-space indentation, self-closing leaf tags, escaped content.
"""

from __future__ import annotations

import re

from .models import Tree, TreeNode, TreeRef
from .utils import warn, xml_escape

INDENT = "  "

# A conservative XML attribute name: ASCII identifier-like, no colon (colon is
# the XML namespace separator). Reserved names are excluded separately.
_VALID_ATTR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
# Only the attributes intrinsic to <n> itself must not be shadowed by a meta
# key. Ref-only attributes (from/to/rel/note) live on <ref>, not <n>, so a
# node meta key like "note" (an xmind topic note) can safely become native.
_RESERVED_ATTRS = {"id", "label", "meta"}


def _format_meta(meta: dict[str, str] | None) -> str:
    """Render a meta dict as ``key:value,key:value`` (escaped), or ''."""
    if not meta:
        return ""
    return ",".join(f"{k}:{v}" for k, v in meta.items())


def _meta_attr_string(meta: dict[str, str] | None, meta_as_attrs: bool) -> str:
    """Render meta as XML attributes appended after id/label.

    When ``meta_as_attrs`` is False, everything goes into a single
    ``meta="k:v,k:v"`` attribute (the default, backward-compatible form).

    When True, each key that is a valid, non-reserved XML attribute name is
    emitted as a native attribute (``type="exact-match"``); keys that aren't
    (spaces, colons, non-ASCII, or reserved names) fall back into ``meta="..."``.
    """
    if not meta:
        return ""

    if not meta_as_attrs:
        return f' meta="{xml_escape(_format_meta(meta))}"'

    native: list[tuple[str, str]] = []
    leftover: dict[str, str] = {}
    for k, v in meta.items():
        if _VALID_ATTR_NAME.match(k) and k not in _RESERVED_ATTRS:
            native.append((k, v))
        else:
            leftover[k] = v

    parts = "".join(f' {k}="{xml_escape(v)}"' for k, v in native)
    if leftover:
        parts += f' meta="{xml_escape(_format_meta(leftover))}"'
    return parts



def _path_to_id(path: list[int], single_root: bool) -> str:
    """Convert a 0-indexed path to a 1-indexed dotted id string.

    With a single root, the root itself is ``1`` and its children are
    ``1.1``, ``1.2`` ... With multiple roots they are ``1``, ``2`` ...
    Either way the rule is the same: increment every index by one and join.
    """
    return ".".join(str(i + 1) for i in path)


def _assign_ids(
    roots: list[TreeNode], single_root: bool
) -> dict[int, str]:
    """Map ``id(node)`` -> dotted id string for every node in the tree."""
    mapping: dict[int, str] = {}

    def walk(node: TreeNode, path: list[int]) -> None:
        mapping[id(node)] = _path_to_id(path, single_root)
        for idx, child in enumerate(node.children):
            walk(child, path + [idx])

    for idx, root in enumerate(roots):
        walk(root, [idx])
    return mapping


def _render_node(
    node: TreeNode,
    node_id: str,
    depth: int,
    id_map: dict[int, str],
    meta_as_attrs: bool,
) -> list[str]:
    """Render a node (and its subtree) to a list of indented XML lines."""
    pad = INDENT * depth
    label = xml_escape(node.label)
    attrs = f'id="{node_id}" label="{label}"'
    attrs += _meta_attr_string(node.meta, meta_as_attrs)

    if not node.children:
        return [f"{pad}<n {attrs} />"]

    lines = [f"{pad}<n {attrs}>"]
    for idx, child in enumerate(node.children):
        child_id = id_map[id(child)]
        lines.extend(_render_node(child, child_id, depth + 1, id_map, meta_as_attrs))
    lines.append(f"{pad}</n>")
    return lines


def _render_ref(ref: TreeRef, id_map_by_path: dict[tuple[int, ...], str]) -> str | None:
    """Render a single ref line, or None if its endpoints don't resolve."""
    from_id = id_map_by_path.get(tuple(ref.from_path))
    to_id = id_map_by_path.get(tuple(ref.to_path))
    if from_id is None or to_id is None:
        warn(
            f"dropping ref with unresolved path: "
            f"from={ref.from_path} to={ref.to_path}"
        )
        return None
    rel = xml_escape(ref.rel) if ref.rel else "see-also"
    line = f'{INDENT}<ref from="{from_id}" to="{to_id}" rel="{rel}"'
    if ref.note:
        line += f' note="{xml_escape(ref.note)}"'
    line += " />"
    return line


def convert(tree: Tree, meta_as_attrs: bool = False) -> str:
    """Serialize a :class:`Tree` to the struct2tree XML string.

    When ``meta_as_attrs`` is True, meta keys that are valid XML attribute
    names are emitted as native attributes instead of a packed ``meta="k:v"``
    string; keys that aren't fall back into ``meta="..."``.
    """
    name = xml_escape(tree.name or "")

    if not tree.roots:
        warn("empty tree: no nodes parsed")
        return f'<tree name="{name}"></tree>'

    single_root = len(tree.roots) == 1
    id_map = _assign_ids(tree.roots, single_root)

    # Build a path-keyed id map for ref resolution.
    id_map_by_path: dict[tuple[int, ...], str] = {}

    def index_paths(node: TreeNode, path: list[int]) -> None:
        id_map_by_path[tuple(path)] = id_map[id(node)]
        for idx, child in enumerate(node.children):
            index_paths(child, path + [idx])

    for idx, root in enumerate(tree.roots):
        index_paths(root, [idx])

    lines = [f'<tree name="{name}">']
    for idx, root in enumerate(tree.roots):
        lines.extend(_render_node(root, id_map[id(root)], 1, id_map, meta_as_attrs))

    if tree.refs:
        lines.append("")  # blank line separating the reference region
        for ref in tree.refs:
            rendered = _render_ref(ref, id_map_by_path)
            if rendered is not None:
                lines.append(rendered)

    lines.append("</tree>")
    return "\n".join(lines)
