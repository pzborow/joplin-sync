import unittest
from pathlib import Path

from joplin_sync.links import joplin_to_local, local_to_joplin
from joplin_sync.sync import safe_filename


class LinkTests(unittest.TestCase):
    def test_joplin_to_local(self):
        body = "[field](:/note-1#field)"
        result = joplin_to_local(body, {"note-1": Path("glossary.md")}, Path("chapter.md"))
        self.assertEqual(result, "[field](glossary.md#field)")

    def test_local_to_joplin(self):
        body = "[field](glossary.md#field)"
        result = local_to_joplin(body, {"glossary.md": "note-1"}, Path("chapter.md"))
        self.assertEqual(result, "[field](:/note-1#field)")

    def test_local_to_joplin_normalizes_parent_paths(self):
        body = "[field](../00 Glossary Elasticsearch.md#field)"
        result = local_to_joplin(
            body,
            {"00 Glossary Elasticsearch.md": "note-1"},
            Path("Deep dive/Analizery językowe i polski tekst.md"),
        )
        self.assertEqual(result, "[field](:/note-1#field)")

    def test_safe_filename_keeps_joplin_title_style(self):
        self.assertEqual(safe_filename("Czym jest Elasticsearch"), "Czym jest Elasticsearch")
        self.assertEqual(safe_filename("01 Czym jest Elasticsearch"), "01 Czym jest Elasticsearch")
        self.assertEqual(safe_filename("Glosariusz Elasticsearch"), "Glosariusz Elasticsearch")
        self.assertEqual(safe_filename("Jak działa wyszukiwanie"), "Jak działa wyszukiwanie")