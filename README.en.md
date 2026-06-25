# struct2tree

[![tests](https://github.com/al0ys1us/struct2tree/actions/workflows/tests.yml/badge.svg)](https://github.com/al0ys1us/struct2tree/actions/workflows/tests.yml)

[English](README.en.md) | [中文](README.md)

A Python CLI tool that converts hierarchical data from many sources (mind maps, file trees, Markdown outlines, JSON, YAML, and more) into a single XML format optimized for LLM readability.

Core value: **denoise, complete, unify**.

- **Denoise**: strip styling, layout, and random IDs — keep only the structural skeleton
- **Complete**: make cross-node references and edge semantics explicit (`<ref>`), which the source formats can't easily express
- **Unify**: no matter the input source, the AI always sees the same schema

Zero external dependencies — standard library only (requires Python 3.10+).

## Installation

```bash
pip install -e .
```

After installation the `struct2tree` command is available globally.

## Output format

```xml
<tree name="Blog System Architecture">
  <n id="1" label="Blog System">
    <n id="1.1" label="User Module">
      <n id="1.1.1" label="Sign Up / Login" meta="auth:OAuth2" />
      <n id="1.1.2" label="Permissions">
        <n id="1.1.2.1" label="Admin" />
        <n id="1.1.2.2" label="Regular User" />
      </n>
    </n>
    <n id="1.2" label="Article Module">
      <n id="1.2.1" label="Editor" meta="format:markdown" />
      <n id="1.2.2" label="Comments" meta="storage:append-only" />
    </n>
  </n>

  <ref from="1.2" to="1.1.2" rel="depends-on" note="Article module relies on permission checks" />
  <ref from="1.2.2" to="1.1" rel="depends-on" />
</tree>
```

- `<tree name="...">`: root element; `name` is the title
- `<n id label meta?>`: a node; `id` is the hierarchical path (`1.2.3`); leaf nodes self-close
- `<ref from to rel note?>`: cross-node reference (a graph edge), grouped in the reference region

## Supported input formats

| Format | Extension / trigger | Notes |
|--------|---------------------|-------|
| Xmind | `.xmind` | New-style `content.json` and legacy `content.xml`, including relationships |
| Markdown | `.md`, `.markdown` | Nested lists, with optional `{meta}` and `[ref]` extension syntax |
| JSON | `.json` | Auto-detects object-nesting (structure A) and path-mapping (structure B) |
| YAML | `.yaml`, `.yml` | Built-in minimal parser supporting mapping / scalar / sequence |
| Indented text | `.txt` | 2 spaces or 1 tab per level |
| Directory-tree text | `--format tree-text` / stdin | `tree` command ASCII box-art output, or indented text |
| Filesystem directory | `--dir <path>` | Recursively scans a directory |

## Usage

```bash
# Auto-detect input format
struct2tree input.xmind
struct2tree outline.md
struct2tree tree.json
struct2tree structure.yaml

# Directory mode
struct2tree --dir ./my-project

# stdin pipe
tree ./src | struct2tree --format tree-text
cat outline.md | struct2tree --format markdown

# Output to file / clipboard
struct2tree input.xmind -o output.xml
struct2tree --dir ./src --clipboard

# Override the tree name
struct2tree input.xmind --name "Blog System Architecture"

# Markdown extension syntax
struct2tree outline.md --parse-meta --parse-ref

# Batch conversion
for f in *.xmind; do struct2tree "$f" -o "${f%.xmind}.xml"; done
```

### All options

```
Positional:
  input                    input file path (format auto-detected). Omit to read from stdin

Options:
  -o, --output <file>      output file path. Defaults to stdout
  --name <string>          set the tree name, overriding auto-inference
  --dir <path>             directory mode: convert a filesystem directory to a tree
  --format <fmt>           force input format: xmind, markdown, json, yaml, text, dir, tree-text
  --sheet <n>              Xmind only: which sheet to process (0-based, default 0)
  --parse-meta             Markdown only: enable {key:value} meta syntax
  --parse-ref              Markdown only: enable [ref] reference-region syntax
  --include-hidden         directory mode: include hidden files and directories
  --ignore <pattern>       directory mode: extra glob pattern to ignore (repeatable)
  --file-meta              directory mode: add size/ext meta to file nodes
  --max-depth <n>          limit maximum recursion depth (unlimited by default)
  --wrap-code-block        wrap the output in a ```xml ... ``` code block
  --clipboard              copy the output to the system clipboard (instead of stdout)
  -v, --version            show the version
  -h, --help               show help
```

### Markdown extension syntax

With `--parse-meta`, a trailing brace on a list item is extracted as meta:

```markdown
- matching strategy {type:greedy, mode:fallback}
```

With `--parse-ref`, a `[ref]` region at the end of the file is parsed into references:

```
[ref]: 1.2 -> 1.1.2 | depends-on | Article module relies on permission checks
```

## Use as a Python library

```python
from struct2tree import convert_source, convert

xml = convert_source("outline.md", parse_meta=True)   # file path -> XML
xml = convert_source("x", fmt="markdown", content="- a\n- b\n")  # text -> XML

# Or operate directly on the internal model
from struct2tree import Tree, TreeNode
xml = convert(Tree(name="t", roots=[TreeNode(label="root")]))
```

## Use within Agents

struct2tree is designed primarily as a preprocessing tool for Agents (Claude Code, Cursor, custom Agents): normalize structured data into a unified XML, then inject it into context. This is more token-efficient and more readable than feeding raw `.xmind` files, directory trees, or messy outlines straight to the model. stdout emits pure XML while warnings and errors go to stderr, so it is pipe-safe.

### Claude Code

The most direct approach is to have Claude Code call it from the terminal and pipe the result into the conversation or the clipboard:

```bash
# Serialize the project structure and copy it, then paste into the chat for code analysis
struct2tree --dir ./src --clipboard

# Convert a mind map to XML and view it
struct2tree design.xmind

# Pipe chaining: convert `tree` output into the unified format
tree ./src | struct2tree --format tree-text
```

You can also wrap it as a slash command. Create `.claude/commands/struct2tree.md` in your project:

```markdown
---
description: Convert a file or directory to struct2tree XML and display it
---

Run `struct2tree $ARGUMENTS` and use the resulting XML as context for further analysis.
```

Then type `/struct2tree ./src` or `/struct2tree design.xmind` in Claude Code.

### Embedding in a prompt / SKILL.md

Use the conversion result as a knowledge skeleton in a system prompt or skill doc:

```bash
# Generate an XML snippet to paste into a section of SKILL.md
struct2tree knowledge.xmind -o skill-tree.xml

# Or wrap it in a code block and copy to the clipboard
struct2tree knowledge.xmind --wrap-code-block --clipboard
```

The `id` in the XML (e.g. `1.2.3`) encodes order, level, and depth, and `<ref>` makes cross-node dependencies explicit, so the model can refer to a node by a path like `1.2.3` when discussing the structure.

### Custom Agents / automation pipelines

Called as a library, it avoids subprocess overhead and fits into pipelines:

```python
from struct2tree import convert_source

# Convert a user-uploaded xmind to XML and splice it into a prompt
tree_xml = convert_source("uploaded.xmind")
prompt = f"Here is the product structure; generate a PRD based on it:\n{tree_xml}"
```

Batch-build a knowledge base:

```bash
for f in docs/*.xmind; do
  struct2tree "$f" -o "build/$(basename "${f%.xmind}").xml"
done
```

## Development & testing

```bash
python3 tests/fixtures/make_xmind_fixtures.py   # generate binary xmind test fixtures
python3 -m unittest discover -s tests -v
```

Tests use only the standard-library `unittest` — no pytest required.

## Architecture

```
struct2tree/
  cli.py            argparse entry point
  converter.py      internal tree -> XML (id assignment, ref-path mapping, escaping, indentation)
  models.py         TreeNode / TreeRef / Tree data models
  detect.py         format auto-detection (by extension + stdin content heuristics)
  utils.py          XML escaping, clipboard, stdin / file reading
  parsers/          per-format parsers, unified parse(source, options) -> Tree
```

Adding a new input format only requires a new parser module (implementing
`parse(source, options) -> Tree`) registered in `parsers/__init__.py`'s
`REGISTRY` and in `detect.py`.

## License

[MIT](LICENSE) © 2026 Aloysius
