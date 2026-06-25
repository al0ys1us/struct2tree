import os
import tempfile
import unittest

import conftest  # noqa: F401

import struct2tree.parsers.directory as d


class TestDirectory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # build a small tree:
        # root/
        #   src/
        #     main.py
        #     a.py
        #   .hidden
        #   __pycache__/
        #     x.pyc
        #   README.md
        os.makedirs(os.path.join(self.tmp, "src"))
        os.makedirs(os.path.join(self.tmp, "__pycache__"))
        for p in [
            "src/main.py",
            "src/a.py",
            ".hidden",
            "__pycache__/x.pyc",
            "README.md",
        ]:
            with open(os.path.join(self.tmp, p), "w") as f:
                f.write("x")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp)

    def parse(self, **opts):
        return d.parse(self.tmp, {"dir": self.tmp, **opts})

    def test_basic_structure(self):
        t = self.parse()
        root = t.roots[0]
        labels = [c.label for c in root.children]
        # dirs first (src), then files (README.md); hidden + pycache excluded
        self.assertEqual(labels, ["src", "README.md"])

    def test_dirs_before_files(self):
        t = self.parse()
        children = t.roots[0].children
        self.assertEqual(children[0].label, "src")  # dir first
        self.assertTrue(children[0].children)  # has children

    def test_alphabetical_within_group(self):
        t = self.parse()
        src = t.roots[0].children[0]
        self.assertEqual([c.label for c in src.children], ["a.py", "main.py"])

    def test_hidden_excluded_by_default(self):
        t = self.parse()
        labels = [c.label for c in t.roots[0].children]
        self.assertNotIn(".hidden", labels)

    def test_include_hidden(self):
        t = self.parse(include_hidden=True)
        labels = [c.label for c in t.roots[0].children]
        self.assertIn(".hidden", labels)

    def test_pycache_excluded(self):
        t = self.parse()
        labels = [c.label for c in t.roots[0].children]
        self.assertNotIn("__pycache__", labels)

    def test_ignore_pattern(self):
        t = self.parse(ignore=["*.md"])
        labels = [c.label for c in t.roots[0].children]
        self.assertNotIn("README.md", labels)

    def test_file_meta(self):
        t = self.parse(file_meta=True)
        readme = [c for c in t.roots[0].children if c.label == "README.md"][0]
        self.assertIn("size", readme.meta)
        self.assertIn("ext", readme.meta)
        self.assertEqual(readme.meta["ext"], ".md")

    def test_max_depth(self):
        t = self.parse(max_depth=1)
        src = t.roots[0].children[0]
        # depth limited: src present but its children pruned
        self.assertEqual(src.label, "src")
        self.assertEqual(len(src.children), 0)

    def test_empty_dir(self):
        empty = tempfile.mkdtemp()
        try:
            t = d.parse(empty, {"dir": empty})
            self.assertEqual(len(t.roots), 1)
            self.assertEqual(len(t.roots[0].children), 0)
        finally:
            os.rmdir(empty)

    def test_not_a_directory_raises(self):
        with self.assertRaises(ValueError):
            d.parse("/nonexistent/path/xyz", {"dir": "/nonexistent/path/xyz"})


if __name__ == "__main__":
    unittest.main()
