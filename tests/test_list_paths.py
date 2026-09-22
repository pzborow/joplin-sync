import unittest

from joplin_sync.list_paths import matching_paths


class ListPathsTests(unittest.TestCase):
    def test_recursive_case_insensitive_matching(self):
        folders = [
            {"id": "private", "title": "Private", "parent_id": ""},
            {"id": "programming", "title": "Programming", "parent_id": "private"},
            {"id": "mongo", "title": "MongoDB", "parent_id": "programming"},
            {"id": "elastic", "title": "Elasticsearch", "parent_id": "programming"},
            {"id": "deep", "title": "Deep dive", "parent_id": "elastic"},
        ]

        self.assertEqual(matching_paths(folders, "mongo"), ["Private / Programming / MongoDB"])
        self.assertEqual(
            matching_paths(folders, "elastic"),
            [
                "Private / Programming / Elasticsearch",
                "Private / Programming / Elasticsearch / Deep dive",
            ],
        )
        self.assertEqual(matching_paths(folders, "DEEP"), ["Private / Programming / Elasticsearch / Deep dive"])
