"""Command-line entry point for struct2tree."""

from __future__ import annotations

import argparse
import sys

from . import __version__, detect
from .converter import convert
from .parsers import get_parser
from .utils import copy_to_clipboard, read_file, read_stdin, warn

VALID_FORMATS = ["xmind", "markdown", "json", "yaml", "text", "dir", "tree-text"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="struct2tree",
        description="Convert hierarchical structures to LLM-readable XML.",
    )
    p.add_argument(
        "input",
        nargs="?",
        help="input file path (format auto-detected). Omit to read stdin.",
    )
    p.add_argument("-o", "--output", help="output file path (default: stdout)")
    p.add_argument("--name", help="tree name, overriding auto-inference")
    p.add_argument("--dir", help="directory mode: convert a filesystem dir")
    p.add_argument(
        "--format",
        choices=VALID_FORMATS,
        help="force input format, skipping auto-detection",
    )
    p.add_argument(
        "--sheet", type=int, default=0, help="xmind: sheet index (default 0)"
    )
    p.add_argument(
        "--parse-meta",
        action="store_true",
        help="markdown: enable {key:value} meta syntax",
    )
    p.add_argument(
        "--parse-ref",
        action="store_true",
        help="markdown: enable [ref] region syntax",
    )
    p.add_argument(
        "--include-hidden",
        action="store_true",
        help="dir: include hidden files and directories",
    )
    p.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="dir: extra glob pattern to ignore (repeatable)",
    )
    p.add_argument(
        "--file-meta",
        action="store_true",
        help="dir: add size/ext meta to file nodes",
    )
    p.add_argument(
        "--max-depth", type=int, help="limit maximum recursion depth"
    )
    p.add_argument(
        "--meta-as-attrs",
        action="store_true",
        help="render meta keys as native XML attributes when valid "
        "(falls back to meta=\"k:v\" otherwise)",
    )
    p.add_argument(
        "--wrap-code-block",
        action="store_true",
        help="wrap output in a ```xml code block",
    )
    p.add_argument(
        "--clipboard",
        action="store_true",
        help="copy output to the system clipboard instead of stdout",
    )
    p.add_argument(
        "-v", "--version", action="version", version=f"struct2tree {__version__}"
    )
    return p


def _resolve_format(args) -> tuple[str, dict]:
    """Determine the format and the source string to hand the parser.

    Returns ``(fmt, options)`` where options carries parser inputs including
    possibly ``content`` (raw text for stdin / text-based parsers).
    """
    options: dict = {
        "name": args.name,
        "sheet": args.sheet,
        "parse_meta": args.parse_meta,
        "parse_ref": args.parse_ref,
        "include_hidden": args.include_hidden,
        "ignore": args.ignore,
        "file_meta": args.file_meta,
        "max_depth": args.max_depth,
        "dir": args.dir,
    }

    # Directory mode wins.
    if args.dir:
        return "dir", options

    # Explicit format.
    if args.format:
        fmt = args.format
    elif args.input:
        fmt = detect.detect_by_extension(args.input)
        if fmt is None:
            # Unknown extension: read content and detect heuristically.
            content = read_file(args.input)
            fmt = detect.detect_by_content(content)
            options["content"] = content
        return fmt, options
    else:
        # stdin
        content = read_stdin()
        options["content"] = content
        fmt = detect.detect_by_content(content)
        return fmt, options

    # Explicit format with a file input: text-based parsers read the path,
    # but stdin still needs content if no input given.
    if not args.input:
        options["content"] = read_stdin()
    return fmt, options


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        fmt, options = _resolve_format(args)
    except OSError as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 1

    source = args.dir or args.input or "<stdin>"

    try:
        parser_mod = get_parser(fmt)
        tree = parser_mod.parse(source, options)
    except FileNotFoundError:
        print(f"error: file not found: {source}", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Parsers raise ValueError (incl. json.JSONDecodeError) for malformed
        # input — report it as a parse error with the parser's message.
        print(f"error: failed to parse {fmt}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Anything else is an unexpected internal error, not bad input. Surface
        # the exception type so it isn't silently disguised as a parse failure.
        print(
            f"error: internal error while parsing {fmt}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    xml = convert(tree, meta_as_attrs=args.meta_as_attrs)
    if args.wrap_code_block:
        xml = f"```xml\n{xml}\n```"

    if args.clipboard:
        try:
            copy_to_clipboard(xml)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print("copied to clipboard", file=sys.stderr)
    elif args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(xml + "\n")
        except OSError as exc:
            print(f"error: cannot write output: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(xml + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
