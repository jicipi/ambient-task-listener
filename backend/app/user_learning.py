from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LEARNING_FILE = DATA_DIR / "user_learning.json"


def _load_learning() -> dict:
    if not LEARNING_FILE.exists():
        return {"categories": {}, "synonyms": {}}
    try:
        with open(LEARNING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"categories": {}, "synonyms": {}}
            data.setdefault("categories", {})
            data.setdefault("synonyms", {})
            return data
    except Exception:
        return {"categories": {}, "synonyms": {}}


def _save_learning(data: dict) -> None:
    with open(LEARNING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def learn_category(item_text: str, category: str) -> None:
    if not item_text or not category:
        return

    data = _load_learning()
    data["categories"][item_text.strip().lower()] = category.strip().lower()
    _save_learning(data)


def get_learned_category(item_text: str) -> str | None:
    if not item_text:
        return None

    data = _load_learning()
    return data["categories"].get(item_text.strip().lower())


def learn_synonym(source_text: str, normalized_text: str) -> None:
    if not source_text or not normalized_text:
        return

    data = _load_learning()
    data["synonyms"][source_text.strip().lower()] = normalized_text.strip().lower()
    _save_learning(data)


def get_learned_synonym(source_text: str) -> str | None:
    if not source_text:
        return None

    data = _load_learning()
    return data["synonyms"].get(source_text.strip().lower())