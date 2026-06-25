import json
import unittest

import conftest  # noqa: F401

import struct2tree.parsers.json_tree as jt


def parse(obj, **opts):
    return jt.parse("x", {"content": json.dumps(obj), **opts})


class TestJSON(unittest.TestCase):
    def test_structure_a(self):
        obj = {
            "name": "博客系统",
            "children": [
                {"name": "用户模块", "children": [{"name": "注册登录"}]},
                {"label": "文章模块"},
            ],
        }
        t = parse(obj)
        self.assertEqual(t.roots[0].label, "博客系统")
        self.assertEqual(t.roots[0].children[0].children[0].label, "注册登录")
        self.assertEqual(t.roots[0].children[1].label, "文章模块")

    def test_structure_a_meta(self):
        obj = {"name": "x", "children": [{"name": "c", "meta": {"k": "v"}}]}
        t = parse(obj)
        self.assertEqual(t.roots[0].children[0].meta, {"k": "v"})

    def test_structure_a_refs(self):
        obj = {
            "name": "root",
            "children": [{"name": "a"}, {"name": "b"}],
            "refs": [{"from": "1.1", "to": "1.2", "rel": "depends-on", "note": "x"}],
        }
        t = parse(obj)
        self.assertEqual(len(t.refs), 1)
        self.assertEqual(t.refs[0].from_path, [0, 0])
        self.assertEqual(t.refs[0].to_path, [0, 1])

    def test_structure_b(self):
        obj = {"博客系统": {"用户模块": {"注册登录": None, "权限管理": {"管理员": None}}}}
        t = parse(obj)
        self.assertEqual(t.roots[0].label, "博客系统")
        self.assertEqual(
            t.roots[0].children[0].children[1].children[0].label, "管理员"
        )

    def test_structure_b_scalar_leaf(self):
        obj = {"k": {"child": "scalar-value"}}
        t = parse(obj)
        self.assertEqual(t.roots[0].children[0].meta, {"value": "scalar-value"})

    def test_single_node(self):
        t = parse({"only": None})
        self.assertEqual(len(t.roots), 1)
        self.assertEqual(t.roots[0].label, "only")

    def test_deep_nesting(self):
        obj = {"1": {"2": {"3": {"4": {"5": {"6": None}}}}}}
        t = parse(obj)
        node = t.roots[0]
        depth = 1
        while node.children:
            node = node.children[0]
            depth += 1
        self.assertEqual(depth, 6)

    def test_array_root_multi(self):
        obj = [{"name": "a"}, {"name": "b"}]
        t = parse(obj)
        self.assertEqual(len(t.roots), 2)

    def test_special_chars(self):
        t = parse({"<x> & \"y\"": None})
        self.assertEqual(t.roots[0].label, "<x> & \"y\"")

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            jt.parse("x", {"content": "{not valid"})


if __name__ == "__main__":
    unittest.main()
