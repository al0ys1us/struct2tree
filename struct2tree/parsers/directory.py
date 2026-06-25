"""Filesystem directory parser (``--dir <path>``).

Recursively scans a directory into a tree: directories before files, each
alphabetically. Hidden entries and common noise dirs are skipped by default.
"""

from __future__ import annotations

import fnmatch
import os

from ..models import Tree, TreeNode

DEFAULT_IGNORES = {
    "node_modules",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
}


def _should_ignore(name: str, options: dict) -> bool:
    if not options.get("include_hidden", False) and name.startswith("."):
        return True
    if name in DEFAULT_IGNORES:
        return True
    for pat in options.get("ignore", []) or []:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def _file_meta(path: str) -> dict[str, str]:
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    ext = os.path.splitext(path)[1]
    return {"size": str(size), "ext": ext}


def _scan(path: str, options: dict, depth: int) -> TreeNode:
    name = os.path.basename(os.path.normpath(path))
    max_depth = options.get("max_depth")

    if not os.path.isdir(path):
        meta = _file_meta(path) if options.get("file_meta") else None
        return TreeNode(label=name, meta=meta)

    node = TreeNode(label=name)
    if max_depth is not None and depth >= max_depth:
        return node

    try:
        entries = list(os.scandir(path))
    except OSError:
        return node

    dirs, files = [], []
    for e in entries:
        if _should_ignore(e.name, options):
            continue
        # Do not follow symlinked directories: a symlink pointing at an
        # ancestor would otherwise recurse infinitely. Treat them as leaves.
        if e.is_symlink():
            files.append(e)
        elif e.is_dir(follow_symlinks=False):
            dirs.append(e)
        else:
            files.append(e)

    dirs.sort(key=lambda e: e.name.lower())
    files.sort(key=lambda e: e.name.lower())

    for e in dirs:
        node.children.append(_scan(e.path, options, depth + 1))
    for e in files:
        meta = _file_meta(e.path) if options.get("file_meta") else None
        node.children.append(TreeNode(label=e.name, meta=meta))

    return node


def parse(source: str, options: dict) -> Tree:
    path = options.get("dir") or source
    if not os.path.isdir(path):
        raise ValueError(f"not a directory: {path}")
    root = _scan(path, options, 0)
    name = options.get("name") or root.label
    return Tree(name=name, roots=[root])
