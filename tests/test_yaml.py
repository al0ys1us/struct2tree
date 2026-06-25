import unittest

import conftest  # noqa: F401

import struct2tree.parsers.yaml_tree as yt


def parse(text, **opts):
    return yt.parse("x", {"content": text, **opts})


class TestYAML(unittest.TestCase):
    def test_basic_mapping(self):
        text = """博客系统:
  用户模块:
    注册登录:
    权限管理:
      管理员:
      普通用户:
  文章模块:
    编辑器:
"""
        t = parse(text)
        self.assertEqual(t.roots[0].label, "博客系统")
        self.assertEqual(t.roots[0].children[0].children[1].children[0].label, "管理员")

    def test_scalar_leaf_to_meta(self):
        text = "root:\n  child: somevalue\n"
        t = parse(text)
        self.assertEqual(t.roots[0].children[0].meta, {"value": "somevalue"})

    def test_sequence(self):
        text = """root:
  items:
    - one
    - two
    - three
"""
        t = parse(text)
        items = t.roots[0].children[0]
        self.assertEqual(len(items.children), 3)
        self.assertEqual(items.children[0].label, "one")

    def test_flow_sequence(self):
        t = parse("root:\n  items: [a, b, c]\n")
        items = t.roots[0].children[0]
        self.assertEqual([c.label for c in items.children], ["a", "b", "c"])

    def test_flow_mapping(self):
        t = parse("root:\n  cfg: {x: 1, y: 2}\n")
        cfg = t.roots[0].children[0]
        self.assertEqual(cfg.children[0].label, "x")
        self.assertEqual(cfg.children[0].meta, {"value": "1"})

    def test_nested_flow(self):
        t = parse("root:\n  m: {a: [1, 2], b: x}\n")
        m = t.roots[0].children[0]
        a = m.children[0]
        self.assertEqual([c.label for c in a.children], ["1", "2"])

    def test_flow_with_quoted_comma(self):
        t = parse('root:\n  items: ["a, b", c]\n')
        items = t.roots[0].children[0]
        self.assertEqual([c.label for c in items.children], ["a, b", "c"])

    def test_single_root(self):
        t = parse("only:\n")
        self.assertEqual(len(t.roots), 1)
        self.assertEqual(t.roots[0].label, "only")

    def test_deep_nesting(self):
        text = "a:\n  b:\n    c:\n      d:\n        e:\n          f:\n"
        t = parse(text)
        node = t.roots[0]
        depth = 1
        while node.children:
            node = node.children[0]
            depth += 1
        self.assertEqual(depth, 6)

    def test_comment_stripped(self):
        text = "root:  # a comment\n  child:\n"
        t = parse(text)
        self.assertEqual(t.roots[0].label, "root")
        self.assertEqual(t.roots[0].children[0].label, "child")

    def test_quoted_key(self):
        text = '"quoted key":\n  child:\n'
        t = parse(text)
        self.assertEqual(t.roots[0].label, "quoted key")

    def test_document_markers_ignored(self):
        text = "---\nroot:\n  child:\n...\n"
        t = parse(text)
        self.assertEqual(t.roots[0].label, "root")

    def test_empty(self):
        t = parse("")
        self.assertEqual(len(t.roots), 0)


if __name__ == "__main__":
    unittest.main()
