import unittest

import conftest  # noqa: F401

import struct2tree.parsers.markdown as md
from struct2tree.converter import convert


def parse(text, **opts):
    return md.parse("x", {"content": text, **opts})


class TestMarkdown(unittest.TestCase):
    def test_basic_nesting(self):
        text = """# Title
- a
  - a1
  - a2
    - a2x
- b
"""
        t = parse(text)
        self.assertEqual(t.name, "Title")
        self.assertEqual(len(t.roots), 2)
        self.assertEqual(t.roots[0].children[1].children[0].label, "a2x")

    def test_single_root(self):
        t = parse("- only\n")
        self.assertEqual(len(t.roots), 1)

    def test_deep_nesting(self):
        text = "- 1\n  - 2\n    - 3\n      - 4\n        - 5\n          - 6\n"
        t = parse(text)
        node = t.roots[0]
        depth = 1
        while node.children:
            node = node.children[0]
            depth += 1
        self.assertEqual(depth, 6)

    def test_multi_root(self):
        t = parse("- r1\n- r2\n- r3\n")
        self.assertEqual(len(t.roots), 3)

    def test_mixed_ordered_unordered(self):
        text = "- a\n  1. one\n  2. two\n"
        t = parse(text)
        self.assertEqual(len(t.roots[0].children), 2)
        self.assertEqual(t.roots[0].children[0].label, "one")

    def test_meta_extension(self):
        text = "- 匹配策略 {type:exact-match, mode:complement}\n"
        t = parse(text, parse_meta=True)
        self.assertEqual(t.roots[0].meta, {"type": "exact-match", "mode": "complement"})
        self.assertEqual(t.roots[0].label, "匹配策略")

    def test_meta_disabled_by_default(self):
        text = "- 匹配策略 {type:exact-match}\n"
        t = parse(text)
        self.assertIsNone(t.roots[0].meta)
        self.assertIn("{type:exact-match}", t.roots[0].label)

    def test_ref_extension(self):
        text = """- a
- b

[ref]: 1 -> 2 | depends-on | a needs b
"""
        t = parse(text, parse_ref=True)
        self.assertEqual(len(t.refs), 1)
        self.assertEqual(t.refs[0].from_path, [0])
        self.assertEqual(t.refs[0].to_path, [1])
        self.assertEqual(t.refs[0].rel, "depends-on")
        self.assertEqual(t.refs[0].note, "a needs b")
        out = convert(t)
        self.assertIn('<ref from="1" to="2" rel="depends-on"', out)

    def test_special_chars(self):
        t = parse("- <tag> & \"q\" 中文 🎯\n")
        out = convert(t)
        self.assertIn("&lt;tag&gt;", out)

    def test_empty(self):
        t = parse("")
        self.assertEqual(len(t.roots), 0)

    def test_non_list_line_in_list_ignored(self):
        text = "- a\nrandom text\n- b\n"
        t = parse(text)
        # the stray line is ignored; a and b remain roots
        self.assertEqual(len(t.roots), 2)


if __name__ == "__main__":
    unittest.main()
