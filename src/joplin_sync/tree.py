from __future__ import annotations

from pathlib import Path

from .api import JoplinApi


def folder_map(api: JoplinApi) -> dict[tuple[str, str], dict]:
    return {(item.get("parent_id", ""), item["title"]): item for item in api.folders()}


def find_path(api: JoplinApi, path: str) -> dict | None:
    current = ""
    folders = folder_map(api)
    found = None
    for part in [x.strip() for x in path.split("/") if x.strip()]:
        found = folders.get((current, part))
        if not found:
            return None
        current = found["id"]
    return found


def ensure_path(api: JoplinApi, path: str, parent_id: str = "") -> dict:
    folders = folder_map(api)
    current = parent_id
    found = None
    for part in [x.strip() for x in path.split("/") if x.strip()]:
        found = folders.get((current, part))
        if not found:
            found = api.create_folder(part, current)
            folders[(current, part)] = found
        current = found["id"]
    return found


def notebook_tree(api: JoplinApi, folder_id: str) -> list[tuple[Path, dict]]:
    result = []

    def walk(current_id: str, relative: Path) -> None:
        for note in api.notes(current_id):
            result.append((relative / f"{note['title']}.md", note))

        folders = [x for x in api.folders() if x.get("parent_id") == current_id]
        for folder in folders:
            walk(folder["id"], relative / folder["title"])

    walk(folder_id, Path())
    return result
