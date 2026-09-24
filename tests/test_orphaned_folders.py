import tempfile
import unittest
from pathlib import Path

from joplin_sync.sync import local_folder_paths, orphaned_folders, publish

FOLDERS = [
    {"id": "root", "title": "Programming", "parent_id": "private"},
    {"id": "arch", "title": "Architecture", "parent_id": "root"},
    {"id": "clean", "title": "clean", "parent_id": "arch"},
    {"id": "cqrs", "title": "cqrs", "parent_id": "arch"},
    {"id": "se", "title": "Software engineering", "parent_id": "root"},
    {"id": "se-arch", "title": "Architecture", "parent_id": "se"},
    {"id": "python", "title": "Python", "parent_id": "root"},
    {"id": "django", "title": "Django", "parent_id": "python"},
]


class OrphanedFoldersTests(unittest.TestCase):
    def test_empty_remote_only_folders_are_listed_children_first(self):
        local = {"Software engineering", "Software engineering/Architecture", "Python"}
        counts = {"se-arch": 3, "python": 2}

        result = orphaned_folders(FOLDERS, "root", local, counts)

        self.assertEqual(
            result,
            [
                ("Architecture/clean", "clean"),
                ("Architecture/cqrs", "cqrs"),
                ("Architecture", "arch"),
                ("Python/Django", "django"),
            ],
        )

    def test_folder_with_notes_is_kept_with_its_parents(self):
        local = {"Software engineering", "Software engineering/Architecture", "Python"}
        counts = {"cqrs": 1}

        result = orphaned_folders(FOLDERS, "root", local, counts)

        self.assertNotIn(("Architecture/cqrs", "cqrs"), result)
        self.assertNotIn(("Architecture", "arch"), result)
        self.assertIn(("Architecture/clean", "clean"), result)

    def test_empty_folder_that_exists_locally_is_kept(self):
        local = {"Architecture", "Architecture/clean", "Architecture/cqrs",
                 "Software engineering", "Software engineering/Architecture", "Python", "Python/Django"}

        self.assertEqual(orphaned_folders(FOLDERS, "root", local, {}), [])

    def test_local_folder_paths_skip_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Databases" / "Search").mkdir(parents=True)
            (root / ".git" / "objects").mkdir(parents=True)
            (root / "Cloud" / ".kilo").mkdir(parents=True)

            self.assertEqual(local_folder_paths(root), {"Databases", "Databases/Search", "Cloud"})


class FakeApi:
    """In-memory stand-in for the Joplin API, enough for publish()."""

    def __init__(self, folders, notes):
        self._folders = [dict(f) for f in folders]
        self._notes = {n["id"]: dict(n) for n in notes}
        self.deleted_folders = []

    def folders(self):
        return list(self._folders)

    def notes(self, folder_id):
        return [n for n in self._notes.values() if n["parent_id"] == folder_id]

    def create_folder(self, title, parent_id):
        folder = {"id": f"f{len(self._folders)}", "title": title, "parent_id": parent_id}
        self._folders.append(folder)
        return folder

    def create_note(self, title, body, parent_id):
        note = {"id": f"n{len(self._notes)}", "title": title, "body": body, "parent_id": parent_id}
        self._notes[note["id"]] = note
        return note

    def update_note(self, note_id, title, body):
        self._notes[note_id].update(title=title, body=body)

    def delete_note(self, note_id):
        del self._notes[note_id]

    def delete_folder(self, folder_id):
        self.deleted_folders.append(folder_id)
        self._folders = [f for f in self._folders if f["id"] != folder_id]


class PublishDeletesMovedNotebooksTests(unittest.TestCase):
    def test_publish_removes_notebook_left_empty_after_move(self):
        api = FakeApi(
            folders=[
                {"id": "private", "title": "Private", "parent_id": ""},
                {"id": "root", "title": "Programming", "parent_id": "private"},
                {"id": "sql", "title": "SQL", "parent_id": "root"},
            ],
            notes=[{"id": "q1", "title": "Joins", "body": "", "parent_id": "sql"}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            moved = root / "Databases" / "RDBMS"
            moved.mkdir(parents=True)
            (moved / "Joins.md").write_text("# Joins\n", encoding="utf-8")

            publish(api, root, "Private/Programming", force=True)

        self.assertEqual(api.deleted_folders, ["sql"])
        self.assertEqual(
            sorted(f["title"] for f in api.folders()),
            ["Databases", "Private", "Programming", "RDBMS"],
        )


if __name__ == "__main__":
    unittest.main()
