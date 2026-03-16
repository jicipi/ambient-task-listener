from __future__ import annotations

import json
import uuid
from pathlib import Path

DATA_DIR = Path("data")
FILES = ["shopping", "todo", "appointments", "ideas"]


def migrate_entry(entry: dict) -> dict:
    # déjà au nouveau format
    if "id" in entry and "text" in entry:
        if "done" not in entry:
            entry["done"] = False
        return entry

    text = entry.get("text") or entry.get("item") or ""

    return {
        "id": str(uuid.uuid4()),
        "text": text,
        "created_at": entry.get("created_at"),
        "source_transcript": entry.get("source_transcript"),
        "done": entry.get("done", False),
    }


def migrate_file(name: str) -> None:
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        print(f"{name}: absent")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    migrated = [migrate_entry(entry) for entry in data]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    print(f"{name}: {len(data)} entrées migrées")


def main() -> None:
    for name in FILES:
        migrate_file(name)


if __name__ == "__main__":
    main()