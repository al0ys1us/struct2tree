import unittest

import conftest  # noqa: F401

import struct2tree.parsers.tree_text as tt


def parse(text, **opts):
    return tt.parse("x", {"content": text, **opts})


BOX = """my-project/
├── src/
│   ├── main.py
│   ├── utils.py
│   └── models/
│       ├── user.py
│       └── order.py
├── tests/
│   └── test_main.py
└── README.md
"""


class TestTreeText(unittest.TestCase):
    def test_box_art_structure(self):
        t = parse(BOX)
        root = t.roots[0]
        self.assertEqual(root.label, "my-project/")
        labels = [c.label for c in root.children]
        self.assertEqual(labels, ["src/", "tests/", "README.md"])

    def test_box_art_depth(self):
        t = parse(BOX)
        src = t.roots[0].children[0]
        models = src.children[2]
        self.assertEqual(models.label, "models/")
        self.assertEqual(len(models.children), 2)
        self.assertEqual(models.children[0].label, "user.py")

    def test_falls_back_to_indented_text(self):
        # No box chars -> delegate to indented-text parser
        text = "root\n  child\n"
        t = parse(text)
        self.assertEqual(t.roots[0].children[0].label, "child")

    def test_files_and_dirs_mixed(self):
        t = parse(BOX)
        src = t.roots[0].children[0]
        file_labels = [c.label for c in src.children]
        self.assertIn("main.py", file_labels)
        self.assertIn("models/", file_labels)

    def test_single_root(self):
        t = parse("solo/\n")
        self.assertEqual(len(t.roots), 1)


if __name__ == "__main__":
    unittest.main()
