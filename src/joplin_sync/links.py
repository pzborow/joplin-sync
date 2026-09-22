from __future__ import annotations

import re
import os
from pathlib import Path
from urllib.parse import quote, unquote

NOTE_LINK = re.compile(r"\]\(:/([^)#]+)(#[^)]*)\)")
LOCAL_LINK = re.compile(r"\]\(([^:/#][^)]*\.md)(#[^)]*)?\)")


def joplin_to_local(body: str, note_paths: dict[str, Path], current: Path) -> str:
    def replace(match: re.Match) -> str:
        note_id, anchor = match.groups()
        target = note_paths.get(note_id)
        if not target:
            return match.group(0)
        relative = os.path.relpath(os.path.normpath(str(target)), start=os.path.normpath(str(current.parent)))
        encoded = quote(Path(relative).as_posix(), safe='/')
        return f"]({encoded}{anchor or ''})"

    return NOTE_LINK.sub(replace, body)


def local_to_joplin(body: str, note_ids: dict[str, str], current: Path) -> str:
    def replace(match: re.Match) -> str:
        target, anchor = match.groups()
        decoded_target = unquote(target)
        resolved = os.path.normpath(os.path.join(str(current.parent), decoded_target))
        note_id = note_ids.get(resolved)
        if not note_id:
            note_id = note_ids.get(os.path.normpath(decoded_target))
        if not note_id:
            return match.group(0)
        return f"](:/{note_id}{anchor or ''})"

    return LOCAL_LINK.sub(replace, body)
