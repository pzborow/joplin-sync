from __future__ import annotations

import argparse
from pathlib import Path

from .api import JoplinApi
from .list_paths import default_config_path, get_folders, load_token, load_url, matching_paths
from .sync import publish, pull


def main() -> None:
    parser = argparse.ArgumentParser(prog="joplin-sync")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List notebook paths matching a fragment")
    list_parser.add_argument("fragment", help="Case-insensitive path fragment")
    list_parser.add_argument("--config", type=Path, default=None)
    list_parser.add_argument("--url", default=None)

    for name in ("pull", "publish"):
        sync_parser = subparsers.add_parser(name)
        sync_parser.add_argument("--path", help="Ścieżka Joplina, np. Programming/Elasticsearch")
        sync_parser.add_argument("--force", action="store_true")
        sync_parser.add_argument("--config", type=Path, default=None)
        sync_parser.add_argument("--url", default=None)

    args = parser.parse_args()
    if args.command == "list":
        token = load_token(args.config)
        folders = get_folders(args.url or load_url(args.config), token)
        for path in matching_paths(folders, args.fragment):
            print(path)
    else:
        token = load_token(args.config)
        client = JoplinApi(args.url or load_url(args.config), token)
        if args.command == "pull":
            pull(client, Path.cwd(), args.path, args.force)
        else:
            publish(client, Path.cwd(), args.path, args.force)


if __name__ == "__main__":
    main()
