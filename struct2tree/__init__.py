"""struct2tree — universal hierarchical-structure serializer for LLMs.

Public library API::

    from struct2tree import convert_source, convert
    xml = convert_source("outline.md")          # path -> XML string
    xml = convert(tree)                          # Tree model -> XML string
"""

from __future__ import annotations

from .converter import convert
from .models import Tree, TreeNode, TreeRef

__version__ = "0.1.0"

__all__ = [
    "convert",
    "convert_source",
    "Tree",
    "TreeNode",
    "TreeRef",
    "__version__",
]


def convert_source(source: str, fmt: str | None = None, **options) -> str:
    """Parse a file (or, with ``content=...`` in options, raw text) and convert.

    ``fmt`` forces a parser; if omitted it is detected from the file extension.
    """
    from . import detect
    from .parsers import get_parser

    if fmt is None:
        fmt = detect.detect_by_extension(source)
        if fmt is None:
            raise ValueError(f"cannot detect format for: {source}")
    parser = get_parser(fmt)
    tree = parser.parse(source, options)
    return convert(tree)
