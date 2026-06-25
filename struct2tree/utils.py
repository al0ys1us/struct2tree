"""Utility helpers: XML escaping, stdin reading, clipboard, file reading."""

from __future__ import annotations

import subprocess
import sys


def xml_escape(text: str) -> str:
    """Escape the five XML special characters for use in attribute values.

    Order matters: ``&`` must be replaced first so it does not double-escape
    the ampersands introduced by the other replacements.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def read_stdin() -> str:
    """Read all of stdin as text."""
    return sys.stdin.read()


def read_file(path: str) -> str:
    """Read a text file as UTF-8, falling back to latin-1 on decode error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


def get_content(source: str, options: dict) -> str:
    """Resolve text content for a parser.

    The CLI passes raw text via ``options['content']`` (used for stdin and for
    text already read by the caller); otherwise ``source`` is a file path.
    """
    if "content" in options:
        return options["content"]
    return read_file(source)


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Uses ``pbcopy`` on macOS, ``xclip`` on Linux, ``clip`` on Windows.
    Raises :class:`RuntimeError` if no clipboard tool is available.
    """
    if sys.platform == "darwin":
        cmd = ["pbcopy"]
    elif sys.platform.startswith("win"):
        cmd = ["clip"]
    else:
        cmd = ["xclip", "-selection", "clipboard"]

    try:
        proc = subprocess.run(
            cmd, input=text.encode("utf-8"), capture_output=True
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Clipboard tool {cmd[0]!r} not found. Install it or use -o."
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"Clipboard command failed: {proc.stderr.decode('utf-8', 'replace')}"
        )


def warn(message: str) -> None:
    """Print a warning to stderr (keeps stdout clean for piping)."""
    print(f"warning: {message}", file=sys.stderr)
