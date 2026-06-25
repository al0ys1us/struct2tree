"""Parser registry.

Each parser exposes a ``parse(source, options) -> Tree`` callable, where
``source`` is either a file path or raw text (parsers that read files take a
path; text-based parsers take the text directly — the CLI handles the routing).

New input formats only need a new module here plus an entry in the registry
and in :mod:`struct2tree.detect`.
"""

from __future__ import annotations

from . import (
    directory,
    json_tree,
    markdown,
    text,
    tree_text,
    xmind,
    yaml_tree,
)

# format name -> module exposing parse(...)
REGISTRY = {
    "xmind": xmind,
    "markdown": markdown,
    "json": json_tree,
    "yaml": yaml_tree,
    "text": text,
    "tree-text": tree_text,
    "dir": directory,
}


def get_parser(fmt: str):
    """Return the parser module for a format name, or raise ValueError."""
    try:
        return REGISTRY[fmt]
    except KeyError:
        raise ValueError(f"unknown format: {fmt!r}")
