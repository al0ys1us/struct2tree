import unittest

import conftest  # noqa: F401

import struct2tree.parsers.text as txt


def parse(text, **opts):
    return txt.parse("x", {"content": text, **opts})


class TestText(unittest.TestCase):
    def test_basic_indent(self):
        text = "root\n  a\n  b\n    b1\n"
        t = parse(text)
        self.assertEqual(t.roots[0].label, "root")
        self.assertEqual(t.roots[0].children[1].children[0].label, "b1")

    def test_tab_indent(self):
        text = "root\n\ta\n\t\ta1\n"
        t = parse(text)
        self.assertEqual(t.roots[0].children[0].children[0].label, "a1")

    def test_single_root(self):
        t = parse("only\n")
        self.assertEqual(len(t.roots), 1)
        self.assertEqual(t.name, "only")

    def test_multi_root(self):
        t = parse("a\nb\nc\n")
        self.assertEqual(len(t.roots), 3)
        self.assertEqual(t.name, "tree")

    def test_blank_lines_ignored(self):
        text = "root\n\n  a\n\n  b\n"
        t = parse(text)
        self.assertEqual(len(t.roots[0].children), 2)

    def test_deep_nesting(self):
        text = "a\n  b\n    c\n      d\n        e\n          f\n"
        t = parse(text)
        node = t.roots[0]
        depth = 1
        while node.children:
            node = node.children[0]
            depth += 1
        self.assertEqual(depth, 6)

    def test_empty(self):
        t = parse("")
        self.assertEqual(len(t.roots), 0)


if __name__ == "__main__":
    unittest.main()
