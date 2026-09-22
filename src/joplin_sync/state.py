from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = ".joplin-sync.json"


def load_state(root: Path) -> dict:
    path = root / STATE_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(root: Path, notebook_path: str, notebook_id: str) -> None:
    state = {
        "notebook_path": notebook_path,
        "notebook_id": notebook_id,
        "local_root": ".",
        "pulled_at": datetime.now(timezone.utc).isoformat(),
    }
    (root / STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
