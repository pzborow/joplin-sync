from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PAGE_LIMIT = 100  # largest page size the Joplin API accepts


class JoplinApi:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, payload: dict | None = None, params: dict | None = None) -> dict:
        query = {"token": self.token, **(params or {})}
        url = f"{self.base_url}{path}?{urlencode(query)}"
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}

    def paginated(self, path: str, params: dict | None = None) -> list[dict]:
        """Collect items from every page of a list endpoint.

        Joplin returns at most PAGE_LIMIT items per call together with a
        has_more flag. Sorting by id keeps pages stable between calls.
        """
        items: list[dict] = []
        page = 1
        while True:
            query = {"order_by": "id", **(params or {}), "page": page, "limit": PAGE_LIMIT}
            data = self.request("GET", path, params=query)
            items += data.get("items", [])
            if not data.get("has_more"):
                return items
            page += 1

    def folders(self) -> list[dict]:
        return self.paginated("/folders", {"fields": "id,parent_id,title"})

    def notes(self, folder_id: str) -> list[dict]:
        return self.paginated(f"/folders/{folder_id}/notes", {"fields": "id,parent_id,title"})

    def note(self, note_id: str) -> dict:
        return self.request("GET", f"/notes/{note_id}", params={"fields": "id,title,body"})

    def create_folder(self, title: str, parent_id: str) -> dict:
        return self.request("POST", "/folders", {"title": title, "parent_id": parent_id})

    def create_note(self, title: str, body: str, parent_id: str) -> dict:
        return self.request("POST", "/notes", {"title": title, "body": body, "parent_id": parent_id})

    def update_note(self, note_id: str, title: str, body: str) -> dict:
        return self.request("PUT", f"/notes/{note_id}", {"title": title, "body": body})

    def delete_folder(self, folder_id: str) -> dict:
        return self.request("DELETE", f"/folders/{folder_id}")

    def delete_note(self, note_id: str) -> dict:
        return self.request("DELETE", f"/notes/{note_id}")
