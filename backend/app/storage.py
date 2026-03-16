from __future__ import annotations

import uuid
import json
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FILES = {
    "shopping": DATA_DIR / "shopping.json",
    "todo": DATA_DIR / "todo.json",
    "todo_pro": DATA_DIR / "todo_pro.json",
    "appointments": DATA_DIR / "appointments.json",
    "ideas": DATA_DIR / "ideas.json",
}

STOP_ITEMS = {
    "oui",
    "ok",
    "okay",
    "merci",
    "salut",
    "bonjour",
    "bonsoir",
    "hein",
    "hum",
    "euh",
    "bah",
}

COMMON_CORRECTIONS = {
    "fondier": "plombier",
    "pombier": "plombier",
    "plombier de main": "plombier",
}

LEADING_ACTION_WORDS = {
    "appeler",
    "envoyer",
    "faire",
    "préparer",
    "traiter",
    "organiser",
    "caler",
    "réserver",
}


def _load_list(list_name: str) -> list:
    path = FILES[list_name]
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_list(list_name: str, data: list) -> None:
    path = FILES[list_name]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_item(text: str) -> str:
    if not text:
        return ""
    return text.strip().lower()


def _apply_common_corrections(text: str) -> str:
    normalized = _normalize_item(text)
    return COMMON_CORRECTIONS.get(normalized, normalized)


def _is_valid_item(text: str) -> bool:
    normalized = _normalize_item(text)

    if not normalized:
        return False

    if len(normalized) < 3:
        return False

    if normalized in STOP_ITEMS:
        return False

    return True


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _canonicalize_for_dedupe(list_name: str, text: str) -> str:
    text = _apply_common_corrections(text)
    text = _normalize_item(text)

    if list_name in ("todo", "todo_pro"):
        words = text.split()

        # enlever un verbe initial type "appeler", "préparer", etc.
        if words and words[0] in LEADING_ACTION_WORDS:
            words.pop(0)

        # enlever les articles initiaux
        while words and words[0] in {"le", "la", "les", "un", "une", "du", "de", "des", "au", "aux"}:
            words.pop(0)

        text = " ".join(words)

    return text


def add_item(list_name: str, item: str, source_transcript: str | None = None) -> bool:
    if list_name not in FILES or not item:
        return False

    corrected_item = _apply_common_corrections(item)

    if not _is_valid_item(corrected_item):
        return False

    data = _load_list(list_name)
    canonical_item = _canonicalize_for_dedupe(list_name, corrected_item)

    for existing in data:
        existing_text = existing.get("text") or existing.get("item") or ""
        existing_canonical = _canonicalize_for_dedupe(list_name, existing_text)

        # doublon exact métier
        if existing_canonical == canonical_item:
            return False

        # doublon proche seulement pour todo / todo_pro
        if list_name in ("todo", "todo_pro"):
            if _similar(existing_canonical, canonical_item) > 0.9:
                return False

    entry = {
        "id": str(uuid.uuid4()),
        "text": corrected_item,
        "created_at": datetime.utcnow().isoformat(),
        "source_transcript": source_transcript,
        "done": False,
    }

    data.append(entry)
    _save_list(list_name, data)
    return True


def get_all_lists() -> dict:
    return {name: _load_list(name) for name in FILES.keys()}


def get_list(list_name: str) -> list:
    if list_name not in FILES:
        return []
    return _load_list(list_name)


def delete_item(list_name: str, item_id: str) -> bool:
    if list_name not in FILES:
        return False

    data = _load_list(list_name)

    new_data = [
        entry for entry in data
        if entry.get("id") != item_id
    ]

    if len(new_data) == len(data):
        return False

    _save_list(list_name, new_data)
    return True


def update_item_done(list_name: str, item_id: str, done: bool) -> bool:
    if list_name not in FILES:
        return False

    data = _load_list(list_name)
    updated = False

    for entry in data:
        if entry.get("id") == item_id:
            entry["done"] = done
            updated = True
            break

    if not updated:
        return False

    _save_list(list_name, data)
    return True


def rename_item(list_name: str, item_id: str, text: str) -> bool:
    if list_name not in FILES or not text:
        return False

    corrected_text = _apply_common_corrections(text)

    if not _is_valid_item(corrected_text):
        return False

    data = _load_list(list_name)
    updated = False

    for entry in data:
        if entry.get("id") == item_id:
            entry["text"] = corrected_text
            updated = True
            break

    if not updated:
        return False

    _save_list(list_name, data)
    return True