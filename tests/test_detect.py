import unittest

import conftest  # noqa: F401

from struct2tree import detect


class TestDetect(unittest.TestCase):
    def test_extension_detection(self):
        self.assertEqual(detect.detect_by_extension("a.xmind"), "xmind")
        self.assertEqual(detect.detect_by_extension("a.md"), "markdown")
        self.assertEqual(detect.detect_by_extension("a.markdown"), "markdown")
        self.assertEqual(detect.detect_by_extension("a.json"), "json")
        self.assertEqual(detect.detect_by_extension("a.yaml"), "yaml")
        self.assertEqual(detect.detect_by_extension("a.yml"), "yaml")
        self.assertEqual(detect.detect_by_extension("a.txt"), "text")
        self.assertIsNone(detect.detect_by_extension("a.unknown"))

    def test_content_json(self):
        self.assertEqual(detect.detect_by_content('{"a": 1}'), "json")
        self.assertEqual(detect.detect_by_content('[1, 2, 3]'), "json")

    def test_content_invalid_json_falls_through(self):
        # starts with { but not valid JSON -> should not be 'json'
        self.assertNotEqual(detect.detect_by_content("{not json at all"), "json")

    def test_content_tree_text(self):
        text = "root/\n├── a\n└── b\n"
        self.assertEqual(detect.detect_by_content(text), "tree-text")

    def test_content_markdown(self):
        self.assertEqual(detect.detect_by_content("- a\n- b\n"), "markdown")
        self.assertEqual(detect.detect_by_content("1. a\n2. b\n"), "markdown")

    def test_content_yaml(self):
        text = "root:\n  child:\n    leaf:\n"
        self.assertEqual(detect.detect_by_content(text), "yaml")

    def test_content_text_fallback(self):
        text = "just\nsome\nlines\n"
        self.assertEqual(detect.detect_by_content(text), "text")

    def test_empty_content(self):
        self.assertEqual(detect.detect_by_content(""), "text")


if __name__ == "__main__":
    unittest.main()
