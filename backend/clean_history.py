from pathlib import Path
import json

from app.cleaning import clean_item
from app.fuzzy_corrector import correct_item

DATA_DIR = Path("data")
FILES = ["shopping", "todo", "appointments", "ideas"]


def normalize_for_key(text: str) -> str:
    text = clean_item(text)
    text = correct_item(text)
    return text.strip().lower()


def clean_list_file(name: str):
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        print(f"{name}: fichier absent")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = set()
    cleaned = []
    removed = 0

    for entry in data:
        item = entry.get("item", "")
        if not item:
            removed += 1
            continue

        normalized = normalize_for_key(item)

        if not normalized:
            removed += 1
            continue

        if normalized in seen:
            removed += 1
            continue

        seen.add(normalized)
        entry["item"] = normalized
        cleaned.append(entry)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"{name}: {len(data)} → {len(cleaned)} ({removed} supprimés)")


def main():
    for name in FILES:
        clean_list_file(name)


if __name__ == "__main__":
    main()