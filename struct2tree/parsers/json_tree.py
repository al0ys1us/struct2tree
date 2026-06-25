"""JSON tree parser (``.json``).

Auto-detects two shapes:
- Structure A: object with name/label/title + ``children`` (nested objects).
- Structure B: path-mapping object where each key is a node and its value is
  either a nested object (children) or a scalar/null (leaf).
"""

from __future__ import annotations

import json

from ..models import Tree, TreeNode, TreeRef
from ..utils import get_content

_LABEL_KEYS = ("name", "label", "title")
_CHILDREN_KEYS = ("children",)
_META_KEYS = ("meta", "attributes", "props")
_REF_KEYS = ("refs", "references")


def _is_structure_a(obj) -> bool:
    """A dict with a label key AND a children key is structure A."""
    if not isinstance(obj, dict):
        return False
    has_label = any(k in obj for k in _LABEL_KEYS)
    has_children = any(k in obj for k in _CHILDREN_KEYS)
    return has_label and has_children


def _first_label(obj: dict) -> str | None:
    for k in _LABEL_KEYS:
        if k in obj and obj[k] is not None:
            return str(obj[k])
    return None


def _meta_from_obj(obj: dict) -> dict[str, str] | None:
    for k in _META_KEYS:
        if k in obj and isinstance(obj[k], dict):
            return {str(mk): str(mv) for mk, mv in obj[k].items()}
    return None


def _id_str_to_path(id_str: str) -> list[int]:
    return [int(p) - 1 for p in str(id_str).strip().split(".") if p.strip()]


def _node_from_a(obj: dict) -> TreeNode:
    label = _first_label(obj) or ""
    meta = _meta_from_obj(obj)
    node = TreeNode(label=label, meta=meta)
    children = None
    for k in _CHILDREN_KEYS:
        if k in obj:
            children = obj[k]
            break
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                node.children.append(_node_from_a(child))
            else:
                node.children.append(TreeNode(label=str(child)))
    return node


def _node_from_b(key, value) -> TreeNode:
    node = TreeNode(label=str(key))
    if isinstance(value, dict):
        for k, v in value.items():
            node.children.append(_node_from_b(k, v))
    elif value is None:
        pass  # leaf
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    node.children.append(_node_from_b(k, v))
            else:
                node.children.append(TreeNode(label=str(item)))
    else:  # scalar string/number
        node.meta = {"value": str(value)}
    return node


def _collect_refs_a(obj: dict, path: list[int], refs: list[TreeRef]) -> None:
    """Walk a structure-A tree collecting any ``refs``/``references`` arrays.

    Ref entries use 1-indexed dotted ids (from/to) like the output schema.
    """
    for k in _REF_KEYS:
        if k in obj and isinstance(obj[k], list):
            for r in obj[k]:
                if not isinstance(r, dict):
                    continue
                f = r.get("from")
                t = r.get("to")
                if f is None or t is None:
                    continue
                refs.append(
                    TreeRef(
                        from_path=_id_str_to_path(f),
                        to_path=_id_str_to_path(t),
                        rel=str(r.get("rel", "see-also")),
                        note=str(r["note"]) if r.get("note") else None,
                    )
                )
    children = obj.get("children")
    if isinstance(children, list):
        for idx, child in enumerate(children):
            if isinstance(child, dict):
                _collect_refs_a(child, path + [idx], refs)


def parse(source: str, options: dict) -> Tree:
    content = get_content(source, options)
    data = json.loads(content)
    name = options.get("name")

    roots: list[TreeNode] = []
    refs: list[TreeRef] = []

    if isinstance(data, list):
        # Array root: each element is a root node (structure A or B-ish dict).
        for item in data:
            if _is_structure_a(item):
                roots.append(_node_from_a(item))
            elif isinstance(item, dict):
                for k, v in item.items():
                    roots.append(_node_from_b(k, v))
            else:
                roots.append(TreeNode(label=str(item)))
    elif _is_structure_a(data):
        roots.append(_node_from_a(data))
        _collect_refs_a(data, [0], refs)
    elif isinstance(data, dict):
        for k, v in data.items():
            roots.append(_node_from_b(k, v))
    else:
        roots.append(TreeNode(label=str(data)))

    if name is None:
        name = roots[0].label if len(roots) == 1 else "tree"

    return Tree(name=name, roots=roots, refs=refs)
