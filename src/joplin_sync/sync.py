from __future__ import annotations

import re
import shutil
from pathlib import Path

from .api import JoplinApi
from .links import joplin_to_local, local_to_joplin
from .state import load_state, save_state
from .tree import ensure_path, find_path

STATE_NAME = ".joplin-sync.json"


def has_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def safe_filename(title: str, index: int | None = None) -> str:
    cleaned = "".join("_" if char in '/\\:*?\"<>|' else char for char in title).strip()
    cleaned = " ".join(cleaned.split())
    return cleaned or "note"


def load_token(config: Path) -> str:
    import os
    token = os.environ.get("JOPLIN_TOKEN")
    if token:
        return token
    for line in config.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("JOPLIN_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Nie znaleziono JOPLIN_TOKEN")


def local_folder_paths(root: Path) -> set[str]:
    """Relative paths of local directories, skipping hidden ones such as .git."""
    paths = set()
    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        relative = path.relative_to(root)
        if has_hidden_part(relative):
            continue
        paths.add(relative.as_posix())
    return paths


def orphaned_folders(
    folders: list[dict], root_id: str, local_paths: set[str], note_counts: dict[str, int]
) -> list[tuple[str, str]]:
    """Remote folders under root_id with no local directory and no notes.

    A folder qualifies only if all of its subfolders qualify too. The result
    lists children before parents, so it can be deleted in order.
    """
    result = []

    def walk(folder_id: str, folder_path: str) -> bool:
        removable = True
        for child in folders:
            if child.get("parent_id") != folder_id:
                continue
            child_path = f"{folder_path}/{child['title']}" if folder_path else child["title"]
            if walk(child["id"], child_path):
                result.append((child_path, child["id"]))
            else:
                removable = False
        return removable and folder_path not in local_paths and note_counts.get(folder_id, 0) == 0

    walk(root_id, "")
    return result


def pull(api: JoplinApi, root: Path, notebook_path: str, force: bool = False) -> None:
    folder = find_path(api, notebook_path)
    if not folder:
        raise RuntimeError(f"Nie znaleziono ścieżki Joplina: {notebook_path}")

    if any(root.iterdir()):
        if not force:
            raise RuntimeError("Katalog docelowy nie jest pusty. Użyj --force.")
        for child in root.iterdir():
            if child.name != STATE_NAME:
                shutil.rmtree(child) if child.is_dir() else child.unlink()

    def walk(folder_id: str, relative: Path) -> None:
        for note in api.notes(folder_id):
            full = api.note(note["id"])
            local = relative / f"{safe_filename(full['title'])}.md"
            local.parent.mkdir(parents=True, exist_ok=True)
            body = joplin_to_local(full.get("body", ""), note_paths, local)
            if not body.startswith("# "):
                body = f"# {full['title']}\n\n{body}"
            local.write_text(body, encoding="utf-8")
        for child in api.folders():
            if child.get("parent_id") == folder_id:
                walk(child["id"], relative / child["title"])

    note_paths = {}
    def collect(folder_id: str, relative: Path) -> None:
        for note in api.notes(folder_id):
            note_paths[note["id"]] = relative / f"{safe_filename(note['title'])}.md"
        for child in api.folders():
            if child.get("parent_id") == folder_id:
                collect(child["id"], relative / child["title"])
    collect(folder["id"], Path())
    walk(folder["id"], Path())
    save_state(root, notebook_path, folder["id"])


def publish(api: JoplinApi, root: Path, notebook_path: str | None, force: bool = False) -> None:
    state = load_state(root)
    path_from_args = notebook_path is not None
    notebook_path = notebook_path or state.get("notebook_path")
    if not notebook_path:
        raise RuntimeError("Brak ścieżki Joplina. Użyj --path albo wykonaj pull.")
    target = find_path(api, notebook_path)
    if target and not force and path_from_args:
        raise RuntimeError("Ścieżka Joplina już istnieje. Użyj --force.")
    if not target:
        parent_path, _, title = notebook_path.rpartition("/")
        parent = find_path(api, parent_path) if parent_path else None
        target = ensure_path(api, title, parent["id"] if parent else "")

    print(f"publish notebook: {notebook_path}")

    files = sorted(path for path in root.rglob("*.md") if not has_hidden_part(path.relative_to(root)))

    folders = api.folders()

    def folder_key(path: str, title: str) -> str:
        return f"{path}/{title}" if path else title

    folder_ids = {"": target["id"]}

    def collect_folders(folder_id: str, folder_path: str = "") -> None:
        for child in folders:
            if child.get("parent_id") == folder_id:
                child_path = folder_key(folder_path, child["title"])
                folder_ids[child_path] = child["id"]
                collect_folders(child["id"], child_path)

    collect_folders(target["id"])

    def ensure_folder(path: str) -> str:
        if path in folder_ids:
            return folder_ids[path]
        parent_path, _, title = path.rpartition("/")
        parent_id = ensure_folder(parent_path)
        folder = ensure_path(api, title, parent_id)
        folder_ids[path] = folder["id"]
        return folder["id"]

    note_ids_by_path = {}
    for folder_path, folder_id in folder_ids.items():
        for note in api.notes(folder_id):
            note_ids_by_path[folder_key(folder_path, note["title"])] = note["id"]

    note_ids = {}
    created_note_paths = set()
    for file in files:
        relative = file.relative_to(root).as_posix()
        folder_path = "/".join(Path(relative).parts[:-1])
        title = file.stem
        note_key = folder_key(folder_path, title)
        note_id = note_ids_by_path.get(note_key)
        if not note_id:
            parent_id = ensure_folder(folder_path)
            note_id = api.create_note(title, "", parent_id)["id"]
            note_ids_by_path[note_key] = note_id
            created_note_paths.add(note_key)
        note_ids[str(file.resolve())] = note_id
    for file in files:
        relative = file.relative_to(root).as_posix()
        folder_path = "/".join(Path(relative).parts[:-1])
        note_key = folder_key(folder_path, file.stem)
        action = "create" if note_key in created_note_paths else "update"
        print(f"{action}: {notebook_path}/{note_key}")
        body = local_to_joplin(file.read_text(encoding="utf-8"), note_ids, file)
        api.update_note(note_ids[str(file.resolve())], file.stem, body)
    save_state(root, notebook_path, target["id"])

    # Synchronize: delete notes from Joplin that don't exist locally
    def delete_orphaned(folder_id: str, folder_path: str = "") -> None:
        # Delete notes in this folder that don't exist locally
        for note in api.notes(folder_id):
            title = note["title"]
            # Check if this note exists in this folder locally
            should_exist = False
            for file in files:
                file_folder = "/".join(file.relative_to(root).parts[:-1])
                if file.stem == title and file_folder == folder_path:
                    should_exist = True
                    break
            if not should_exist:
                print(f"delete: {notebook_path}/{folder_key(folder_path, title)}")
                api.delete_note(note["id"])
        
        # Recurse into child folders
        for child in api.folders():
            if child.get("parent_id") == folder_id:
                new_path = f"{folder_path}/{child['title']}" if folder_path else child["title"]
                delete_orphaned(child["id"], new_path)
    
    delete_orphaned(target["id"])

    # Synchronize: delete notebooks that don't exist locally and are now empty
    folders = api.folders()

    def subtree_ids(folder_id: str) -> list[str]:
        ids = [folder_id]
        for child in folders:
            if child.get("parent_id") == folder_id:
                ids += subtree_ids(child["id"])
        return ids

    note_counts = {folder_id: len(api.notes(folder_id)) for folder_id in subtree_ids(target["id"])}
    for folder_path, folder_id in orphaned_folders(folders, target["id"], local_folder_paths(root), note_counts):
        print(f"delete folder: {notebook_path}/{folder_path}")
        api.delete_folder(folder_id)
