"""Xmind file parser (``.xmind``).

A ``.xmind`` file is a ZIP archive. Newer versions store ``content.json``;
older versions (pre-2020) store ``content.xml``. We read the requested sheet's
root topic, recurse through attached children, and map relationships onto refs.

All layout/style/id fields are intentionally discarded — only structure and
semantic content survive.
"""

from __future__ import annotations

import json
import zipfile
import xml.etree.ElementTree as ET

from ..models import Tree, TreeNode, TreeRef
from ..utils import warn


def _topic_to_node(
    topic: dict, path: list[int], id_index: dict[str, list[int]]
) -> TreeNode:
    """Convert a content.json topic dict into a :class:`TreeNode`.

    Records each topic's xmind id -> path in ``id_index`` so relationships can
    be resolved to our positional paths afterward.
    """
    label = topic.get("title", "") or ""
    meta: dict[str, str] = {}

    notes = topic.get("notes")
    if isinstance(notes, dict):
        # notes.plain.content is the common shape
        plain = notes.get("plain")
        if isinstance(plain, dict) and plain.get("content"):
            meta["note"] = str(plain["content"]).replace("\n", " ").strip()

    labels = topic.get("labels")
    if isinstance(labels, list) and labels:
        meta["tags"] = "+".join(str(x) for x in labels)

    node = TreeNode(label=label, meta=(meta or None))

    xid = topic.get("id")
    if xid is not None:
        id_index[str(xid)] = path

    children = topic.get("children")
    if isinstance(children, dict):
        attached = children.get("attached")
        if isinstance(attached, list):
            for idx, child in enumerate(attached):
                if isinstance(child, dict):
                    node.children.append(
                        _topic_to_node(child, path + [idx], id_index)
                    )
    return node


def _parse_json_sheet(sheet: dict) -> Tree:
    id_index: dict[str, list[int]] = {}
    root_topic = sheet.get("rootTopic")
    roots: list[TreeNode] = []
    if isinstance(root_topic, dict):
        roots.append(_topic_to_node(root_topic, [0], id_index))

    name = sheet.get("title") or (roots[0].label if roots else "tree")

    refs: list[TreeRef] = []
    relationships = sheet.get("relationships")
    if isinstance(relationships, list):
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            src = rel.get("end1Id") or rel.get("sourceId")
            tgt = rel.get("end2Id") or rel.get("targetId")
            from_path = id_index.get(str(src))
            to_path = id_index.get(str(tgt))
            if from_path is None or to_path is None:
                warn(f"xmind relationship endpoints not found: {src} -> {tgt}")
                continue
            title = rel.get("title")
            refs.append(
                TreeRef(
                    from_path=from_path,
                    to_path=to_path,
                    rel=(title.strip() if title else "see-also"),
                    note=None,
                )
            )

    return Tree(name=name, roots=roots, refs=refs)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _xml_topic_to_node(elem, path: list[int], id_index: dict[str, list[int]]) -> TreeNode:
    """Convert an old-format ``content.xml`` <topic> element to a node."""
    label = ""
    children_container = None
    for child in elem:
        tag = _strip_ns(child.tag)
        if tag == "title":
            label = (child.text or "").strip()
        elif tag == "children":
            children_container = child

    node = TreeNode(label=label)
    xid = elem.get("id")
    if xid:
        id_index[xid] = path

    if children_container is not None:
        # <children><topics><topic>...
        idx = 0
        for topics in children_container:
            if _strip_ns(topics.tag) != "topics":
                continue
            for topic in topics:
                if _strip_ns(topic.tag) == "topic":
                    node.children.append(
                        _xml_topic_to_node(topic, path + [idx], id_index)
                    )
                    idx += 1
    return node


def _parse_xml(data: bytes) -> Tree:
    id_index: dict[str, list[int]] = {}
    root = ET.fromstring(data)
    # find the first sheet
    sheets = [e for e in root.iter() if _strip_ns(e.tag) == "sheet"]
    if not sheets:
        return Tree(name="tree", roots=[])
    sheet = sheets[0]

    roots: list[TreeNode] = []
    for child in sheet:
        if _strip_ns(child.tag) == "topic":
            roots.append(_xml_topic_to_node(child, [0], id_index))
            break

    title_el = next(
        (e for e in sheet if _strip_ns(e.tag) == "title"), None
    )
    name = (title_el.text.strip() if title_el is not None and title_el.text
            else (roots[0].label if roots else "tree"))

    refs: list[TreeRef] = []
    for rel in sheet:
        if _strip_ns(rel.tag) != "relationship":
            continue
        src = rel.get("end1") or rel.get("sourceId")
        tgt = rel.get("end2") or rel.get("targetId")
        fp, tp = id_index.get(src), id_index.get(tgt)
        if fp is None or tp is None:
            continue
        title_child = next(
            (c for c in rel if _strip_ns(c.tag) == "title"), None
        )
        rel_name = (title_child.text.strip()
                    if title_child is not None and title_child.text else "see-also")
        refs.append(TreeRef(from_path=fp, to_path=tp, rel=rel_name))

    return Tree(name=name, roots=roots, refs=refs)


def parse(source: str, options: dict) -> Tree:
    sheet_idx = options.get("sheet", 0)
    name_override = options.get("name")

    try:
        zf = zipfile.ZipFile(source)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(f"cannot open xmind file as zip: {exc}") from exc

    with zf:
        names = zf.namelist()
        if "content.json" in names:
            raw = zf.read("content.json")
            sheets = json.loads(raw)
            if not isinstance(sheets, list):
                sheets = [sheets]
            if sheet_idx >= len(sheets):
                raise ValueError(
                    f"sheet index {sheet_idx} out of range "
                    f"(file has {len(sheets)} sheet(s))"
                )
            tree = _parse_json_sheet(sheets[sheet_idx])
        elif "content.xml" in names:
            tree = _parse_xml(zf.read("content.xml"))
        else:
            raise ValueError(
                "xmind file contains neither content.json nor content.xml"
            )

    if name_override:
        tree.name = name_override
    return tree
