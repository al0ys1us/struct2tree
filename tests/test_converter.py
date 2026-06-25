import unittest

import conftest  # noqa: F401  (sets up sys.path)

from struct2tree.converter import convert
from struct2tree.models import Tree, TreeNode, TreeRef


class TestConverter(unittest.TestCase):
    def test_single_root_ids(self):
        tree = Tree(
            name="t",
            roots=[
                TreeNode(
                    label="root",
                    children=[
                        TreeNode(label="a"),
                        TreeNode(label="b", children=[TreeNode(label="b1")]),
                    ],
                )
            ],
        )
        out = convert(tree)
        self.assertIn('<n id="1" label="root">', out)
        self.assertIn('<n id="1.1" label="a" />', out)
        self.assertIn('<n id="1.2" label="b">', out)
        self.assertIn('<n id="1.2.1" label="b1" />', out)

    def test_multi_root_ids(self):
        tree = Tree(
            name="t",
            roots=[TreeNode(label="first"), TreeNode(label="second")],
        )
        out = convert(tree)
        self.assertIn('<n id="1" label="first" />', out)
        self.assertIn('<n id="2" label="second" />', out)

    def test_self_closing_vs_pair(self):
        tree = Tree(name="t", roots=[TreeNode(label="r", children=[TreeNode(label="c")])])
        out = convert(tree)
        self.assertIn('<n id="1" label="r">', out)
        self.assertIn("</n>", out)
        self.assertIn('<n id="1.1" label="c" />', out)

    def test_meta_rendering(self):
        tree = Tree(
            name="t",
            roots=[TreeNode(label="x", meta={"type": "a", "mode": "b"})],
        )
        out = convert(tree)
        self.assertIn('meta="type:a,mode:b"', out)

    def test_ref_path_to_id(self):
        # root with two children; ref between them
        tree = Tree(
            name="t",
            roots=[
                TreeNode(
                    label="root",
                    children=[TreeNode(label="a"), TreeNode(label="b")],
                )
            ],
            refs=[TreeRef(from_path=[0, 0], to_path=[0, 1], rel="depends-on")],
        )
        out = convert(tree)
        self.assertIn('<ref from="1.1" to="1.2" rel="depends-on" />', out)

    def test_ref_with_note(self):
        tree = Tree(
            name="t",
            roots=[TreeNode(label="r", children=[TreeNode(label="a"), TreeNode(label="b")])],
            refs=[TreeRef(from_path=[0, 0], to_path=[0, 1], rel="reads", note="hi")],
        )
        out = convert(tree)
        self.assertIn('note="hi"', out)

    def test_unresolved_ref_dropped(self):
        tree = Tree(
            name="t",
            roots=[TreeNode(label="r")],
            refs=[TreeRef(from_path=[0], to_path=[9, 9], rel="x")],
        )
        out = convert(tree)
        self.assertNotIn("<ref", out)

    def test_indentation(self):
        tree = Tree(name="t", roots=[TreeNode(label="r", children=[TreeNode(label="c")])])
        out = convert(tree)
        lines = out.splitlines()
        # child line indented by 4 spaces (depth 2 * 2)
        child_line = [l for l in lines if "1.1" in l][0]
        self.assertTrue(child_line.startswith("    <n"))

    def test_xml_escaping(self):
        tree = Tree(name='a & "b"', roots=[TreeNode(label="<x> & 'y'")])
        out = convert(tree)
        self.assertIn("&amp;", out)
        self.assertIn("&lt;x&gt;", out)
        self.assertIn("&apos;y&apos;", out)
        self.assertIn("&quot;", out)

    def test_empty_tree(self):
        tree = Tree(name="empty", roots=[])
        out = convert(tree)
        self.assertEqual(out, '<tree name="empty"></tree>')

    def test_emoji_label(self):
        tree = Tree(name="t", roots=[TreeNode(label="🚀 launch")])
        out = convert(tree)
        self.assertIn("🚀 launch", out)


if __name__ == "__main__":
    unittest.main()
