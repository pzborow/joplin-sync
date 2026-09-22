from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


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

    def folders(self) -> list[dict]:
        return self.request("GET", "/folders").get("items", [])

    def notes(self, folder_id: str) -> list[dict]:
        return self.request("GET", f"/folders/{folder_id}/notes").get("items", [])

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
