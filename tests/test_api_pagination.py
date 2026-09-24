import unittest

from joplin_sync.api import PAGE_LIMIT, JoplinApi


class PagedApi(JoplinApi):
    """JoplinApi with request() answered from memory, page by page."""

    def __init__(self, items):
        super().__init__("http://joplin.test", "token")
        self._items = items
        self.calls = []

    def request(self, method, path, payload=None, params=None):
        self.calls.append((method, path, dict(params or {})))
        page, limit = params["page"], params["limit"]
        chunk = self._items[(page - 1) * limit: page * limit]
        return {"items": chunk, "has_more": page * limit < len(self._items)}


class PaginationTests(unittest.TestCase):
    def test_folders_are_collected_from_all_pages(self):
        items = [{"id": f"f{i:03}", "title": f"Folder {i}", "parent_id": ""} for i in range(250)]
        api = PagedApi(items)

        self.assertEqual(api.folders(), items)
        self.assertEqual([call[2]["page"] for call in api.calls], [1, 2, 3])

    def test_notes_request_the_largest_page_and_stable_order(self):
        api = PagedApi([{"id": "n1", "title": "A", "parent_id": "f1"}])

        api.notes("f1")

        method, path, params = api.calls[0]
        self.assertEqual((method, path), ("GET", "/folders/f1/notes"))
        self.assertEqual(params["limit"], PAGE_LIMIT)
        self.assertEqual(params["order_by"], "id")
        self.assertEqual(params["fields"], "id,parent_id,title")

    def test_single_page_makes_one_call(self):
        api = PagedApi([{"id": "n1", "title": "A", "parent_id": "f1"}])

        self.assertEqual(len(api.notes("f1")), 1)
        self.assertEqual(len(api.calls), 1)

    def test_exactly_full_page_stops_when_has_more_is_false(self):
        items = [{"id": f"n{i:03}", "title": str(i), "parent_id": "f1"} for i in range(PAGE_LIMIT)]
        api = PagedApi(items)

        self.assertEqual(len(api.notes("f1")), PAGE_LIMIT)
        self.assertEqual(len(api.calls), 1)


if __name__ == "__main__":
    unittest.main()
