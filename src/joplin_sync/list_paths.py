from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def default_config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "joplin-sync" / "config"


def load_token(config_path: Path | None = None) -> str:
    token = os.environ.get("JOPLIN_TOKEN")
    if token:
        return token
    config_path = config_path or default_config_path()
    if not config_path.exists():
        raise RuntimeError(f"Nie znaleziono tokenu. Ustaw JOPLIN_TOKEN albo utwórz {config_path}")
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("JOPLIN_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Nie znaleziono JOPLIN_TOKEN")


def load_url(config_path: Path | None = None) -> str:
    url = os.environ.get("JOPLIN_URL")
    if url:
        return url.rstrip("/")
    config_path = config_path or default_config_path()
    if config_path.exists():
        for line in config_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("JOPLIN_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
    return "http://127.0.0.1:41184"


def get_folders(base_url: str, token: str) -> list[dict]:
    query = urlencode({"token": token, "fields": "id,title,parent_id"})
    with urlopen(Request(f"{base_url}/folders?{query}"), timeout=20) as response:
        return json.load(response)["items"]


def matching_paths(folders: list[dict], fragment: str) -> list[str]:
    children: dict[str, list[dict]] = {}
    for folder in folders:
        children.setdefault(folder.get("parent_id", ""), []).append(folder)

    result: list[str] = []
    needle = fragment.casefold()

    def walk(parent_id: str, path: list[str]) -> None:
        for folder in sorted(children.get(parent_id, []), key=lambda item: item["title"].casefold()):
            current = path + [folder["title"]]
            if needle in " / ".join(current).casefold():
                result.append(" / ".join(current))
            walk(folder["id"], current)

    walk("", [])
    return result
