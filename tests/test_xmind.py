import os
import unittest

import conftest  # noqa: F401

import struct2tree.parsers.xmind as x
from struct2tree.converter import convert

FIX = conftest.FIXTURES


class TestXmind(unittest.TestCase):
    def test_basic_structure(self):
        t = x.parse(os.path.join(FIX, "basic.xmind"), {})
        self.assertEqual(t.name, "博客系统架构")
        self.assertEqual(t.roots[0].label, "博客系统")
        self.assertEqual(t.roots[0].children[0].label, "用户模块")

    def test_notes_become_meta(self):
        t = x.parse(os.path.join(FIX, "basic.xmind"), {})
        account = t.roots[0].children[0]
        self.assertEqual(account.meta["note"], "核心模块")

    def test_labels_become_tags(self):
        t = x.parse(os.path.join(FIX, "basic.xmind"), {})
        login = t.roots[0].children[0].children[0]
        self.assertEqual(login.meta["tags"], "OAuth2")

    def test_relationships(self):
        t = x.parse(os.path.join(FIX, "basic.xmind"), {})
        self.assertEqual(len(t.refs), 1)
        out = convert(t)
        self.assertIn('<ref from="1.2" to="1.1.2" rel="depends-on" />', out)

    def test_multi_sheet_default_first(self):
        t = x.parse(os.path.join(FIX, "multi.xmind"), {})
        self.assertEqual(t.roots[0].label, "First")

    def test_multi_sheet_select(self):
        t = x.parse(os.path.join(FIX, "multi.xmind"), {"sheet": 1})
        self.assertEqual(t.roots[0].label, "Second")
        self.assertEqual(t.roots[0].children[0].label, "Child")

    def test_sheet_out_of_range(self):
        with self.assertRaises(ValueError):
            x.parse(os.path.join(FIX, "multi.xmind"), {"sheet": 5})

    def test_legacy_xml_format(self):
        t = x.parse(os.path.join(FIX, "legacy.xmind"), {})
        self.assertEqual(t.roots[0].label, "Old Root")
        self.assertEqual(t.roots[0].children[1].label, "Beta")
        self.assertEqual(t.roots[0].children[1].children[0].label, "Gamma")

    def test_bad_zip_raises(self):
        with self.assertRaises(ValueError):
            x.parse(os.path.join(FIX, "make_xmind_fixtures.py"), {})

    def test_summary_becomes_node_and_refs(self):
        t = x.parse(os.path.join(FIX, "summary.xmind"), {})
        parent = t.roots[0]
        # summary topic appended after the 3 attached subtopics
        self.assertEqual(len(parent.children), 4)
        summary_node = parent.children[3]
        self.assertEqual(summary_node.label, "前两项=核心能力")
        self.assertEqual(summary_node.meta.get("role"), "summary")

    def test_summary_refs_cover_correct_range(self):
        t = x.parse(os.path.join(FIX, "summary.xmind"), {})
        summarizes = [r for r in t.refs if r.rel == "summarizes"]
        # covers subtopics a (index 0) and b (index 1), not c
        self.assertEqual(len(summarizes), 2)
        out = convert(t)
        self.assertIn('<ref from="1.4" to="1.1" rel="summarizes" />', out)
        self.assertIn('<ref from="1.4" to="1.2" rel="summarizes" />', out)
        self.assertNotIn('to="1.3" rel="summarizes"', out)


if __name__ == "__main__":
    unittest.main()
