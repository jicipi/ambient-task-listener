from __future__ import annotations

import uuid
import json
import threading
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from app.cleaning import parse_shopping_item
from app.unit_conversion import units_are_compatible, merge_quantities
from app.date_parser import parse_french_date


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PENDING_FILE = DATA_DIR / "pending.json"
LEARNING_FILE = DATA_DIR / "user_learning.json"

FILES = {
    "shopping": DATA_DIR / "shopping.json",
    "todo": DATA_DIR / "todo.json",
    "todo_pro": DATA_DIR / "todo_pro.json",
    "appointments": DATA_DIR / "appointments.json",
    "ideas": DATA_DIR / "ideas.json",
}

# RLock (reentrant) : certaines fonctions publiques s'appellent entre elles
# (ex: approve_pending_item → add_item)
_lock = threading.RLock()

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


# =========================
# Pending
# =========================

def _load_pending() -> list:
    if not PENDING_FILE.exists():
        return []
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_pending(data: list) -> None:
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_pending_items() -> list[dict]:
    return _load_pending()


def add_pending_item(action: dict) -> None:
    list_name = action.get("list")
    item = action.get("item")
    transcript = action.get("transcript")

    parsed = parse_shopping_item(item) if list_name == "shopping" and item else None

    # Parse scheduled_date for appointments
    scheduled_date: str | None = None
    intent = action.get("intent")
    if intent == "appointment_add" and transcript:
        scheduled_date = parse_french_date(transcript)

    entry = {
        "id": str(uuid.uuid4()),
        "transcript": transcript,
        "intent": intent,
        "item": parsed["text"] if parsed else item,
        "quantity": parsed["quantity"] if parsed else None,
        "unit": parsed["unit"] if parsed else None,
        "list": list_name,
        "confidence": action.get("confidence"),
        "time_hint": action.get("time_hint"),
        "scheduled_date": scheduled_date,
        "source": action.get("source"),
        "decision": action.get("decision"),
        "created_at": datetime.utcnow().isoformat(),
    }

    with _lock:
        data = _load_pending()
        data.append(entry)
        _save_pending(data)


def reject_pending_item(item_id: str) -> bool:
    with _lock:
        data = _load_pending()
        new_data = [entry for entry in data if entry.get("id") != item_id]

        if len(new_data) == len(data):
            return False

        _save_pending(new_data)
        return True


def approve_pending_item(
    item_id: str,
    override_text: str | None = None,
    override_list: str | None = None,
    override_quantity: int | None = None,
    override_unit: str | None = None,
) -> bool:
    with _lock:
        data = _load_pending()

        target = None
        remaining = []

        for entry in data:
            if entry.get("id") == item_id:
                target = entry
            else:
                remaining.append(entry)

        if target is None:
            return False

        list_name = override_list or target.get("list")
        item = override_text or target.get("item")
        quantity = override_quantity if override_quantity is not None else target.get("quantity")
        unit = override_unit if override_unit is not None else target.get("unit")
        transcript = target.get("transcript")
        scheduled_date = target.get("scheduled_date")

        if not list_name or not item:
            return False

        add_item(
            list_name,
            item,
            transcript,
            quantity=quantity,
            unit=unit,
            scheduled_date=scheduled_date,
        )

        _save_pending(remaining)
        return True


# =========================
# Lists
# =========================

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

        if words and words[0] in LEADING_ACTION_WORDS:
            words.pop(0)

        while words and words[0] in {"le", "la", "les", "un", "une", "du", "de", "des", "au", "aux"}:
            words.pop(0)

        text = " ".join(words)

    return text


# =========================
# Add item (core)
# =========================

def add_item(
    list_name: str,
    item: str,
    source_transcript: str | None = None,
    quantity: int | None = None,
    unit: str | None = None,
    scheduled_date: str | None = None,
) -> bool:
    if list_name not in FILES or not item:
        return False

    corrected_item = _apply_common_corrections(item)
    corrected_item = apply_synonym(corrected_item)

    if not _is_valid_item(corrected_item):
        return False

    category = None
    final_text = corrected_item

    if list_name == "shopping":
        parsed = parse_shopping_item(corrected_item)
        final_text = parsed["text"]
        quantity = quantity if quantity is not None else parsed["quantity"]
        unit = unit if unit is not None else parsed["unit"]
        category = parsed.get("category")

    with _lock:
        data = _load_list(list_name)
        canonical_item = _canonicalize_for_dedupe(list_name, final_text)

        for existing in data:
            existing_text = existing.get("text") or existing.get("item") or ""
            existing_canonical = _canonicalize_for_dedupe(list_name, existing_text)

            if existing_canonical != canonical_item:
                continue

            if list_name == "shopping":
                existing_quantity = existing.get("quantity")
                existing_unit = existing.get("unit")

                units_compatible = units_are_compatible(existing_unit, unit)

                # 1) Fusion classique : deux quantités, unités compatibles
                if (
                    quantity is not None
                    and existing_quantity is not None
                    and units_compatible
                ):
                    merged = merge_quantities(existing_quantity, existing_unit, quantity, unit)
                    if merged is not None:
                        new_qty, new_unit = merged
                        existing["quantity"] = new_qty
                        existing["unit"] = new_unit
                    else:
                        existing["quantity"] = existing_quantity + quantity
                    existing["text"] = final_text

                    if category:
                        existing["category"] = category
                        learn_category(final_text, category)

                    _save_list(list_name, data)
                    return True

                # 2) Enrichissement : ancien sans quantité, nouveau avec quantité,
                # seulement si unités compatibles
                if (
                    quantity is not None
                    and existing_quantity is None
                    and units_compatible
                ):
                    existing["text"] = final_text
                    existing["quantity"] = quantity
                    existing["unit"] = unit

                    if category:
                        existing["category"] = category
                        learn_category(final_text, category)

                    _save_list(list_name, data)
                    return True

                # 3) Nouveau sans quantité, ancien avec quantité ET sans unité
                # ex: "poires" + "10 poires" => on garde 10 poires
                if (
                    quantity is None
                    and existing_quantity is not None
                    and existing_unit is None
                ):
                    existing["text"] = final_text

                    if category:
                        existing["category"] = category
                        learn_category(final_text, category)

                    _save_list(list_name, data)
                    return True

                # 4) Deux items sans quantité
                if quantity is None and existing_quantity is None:
                    existing["text"] = final_text

                    if category:
                        existing["category"] = category
                        learn_category(final_text, category)

                    _save_list(list_name, data)
                    return True

                # 5) Sinon, unités incompatibles → ne pas fusionner, continuer la recherche
                continue

        # For appointments: parse scheduled_date from transcript if not provided
        if list_name == "appointments" and scheduled_date is None and source_transcript:
            scheduled_date = parse_french_date(source_transcript)

        entry = {
            "id": str(uuid.uuid4()),
            "text": final_text,
            "quantity": quantity,
            "unit": unit,
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
            "source_transcript": source_transcript,
            "scheduled_date": scheduled_date if list_name == "appointments" else None,
            "done": False,
        }

        data.append(entry)
        _save_list(list_name, data)
        return True


# =========================
# Public API
# =========================

def get_all_lists() -> dict:
    return {name: _load_list(name) for name in FILES.keys()}


def get_list(list_name: str) -> list:
    if list_name not in FILES:
        return []
    return _load_list(list_name)


def delete_item(list_name: str, item_id: str) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        data = _load_list(list_name)
        new_data = [entry for entry in data if entry.get("id") != item_id]

        if len(new_data) == len(data):
            return False

        _save_list(list_name, new_data)
        return True


def update_item_done(list_name: str, item_id: str, done: bool) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        data = _load_list(list_name)

        for entry in data:
            if entry.get("id") == item_id:
                entry["done"] = done
                _save_list(list_name, data)
                return True

    return False


def rename_item(list_name: str, item_id: str, text: str) -> bool:
    if list_name not in FILES or not text:
        return False

    corrected_text = _apply_common_corrections(text)

    if not _is_valid_item(corrected_text):
        return False

    if list_name == "shopping":
        data = _load_list(list_name)

        for entry in data:
            if entry.get("id") == item_id:
                return update_shopping_item(
                    item_id=item_id,
                    text=corrected_text,
                    quantity=None,
                    unit=None,
                    category=entry.get("category"),
                )
        return False

    data = _load_list(list_name)

    for entry in data:
        if entry.get("id") == item_id:
            entry["text"] = corrected_text
            _save_list(list_name, data)
            return True

    return False
    

def update_item_category(list_name: str, item_id: str, category: str) -> bool:
    if list_name != "shopping" or not category:
        return False

    data = _load_list(list_name)

    for entry in data:
        if entry.get("id") == item_id:
            return update_shopping_item(
                item_id=item_id,
                text=entry.get("text", ""),
                quantity=entry.get("quantity"),
                unit=entry.get("unit"),
                category=category,
            )

    return False



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


def learn_synonym(original: str, normalized: str) -> None:
    if not original or not normalized:
        return

    data = _load_learning()
    data["synonyms"][original.strip().lower()] = normalized.strip().lower()
    _save_learning(data)


def _normalize_category(category: str | None) -> str:
    if not category:
        return "autres"
    return category.strip().lower()


def _shopping_items_can_merge(a: dict, b: dict) -> bool:
    text_a = _normalize_item(a.get("text", ""))
    text_b = _normalize_item(b.get("text", ""))

    if text_a != text_b:
        return False

    unit_a = a.get("unit")
    unit_b = b.get("unit")

    return units_are_compatible(unit_a, unit_b)


def _merge_shopping_entries(target: dict, source: dict) -> None:
    qty_target = target.get("quantity")
    qty_source = source.get("quantity")

    unit_target = target.get("unit")
    unit_source = source.get("unit")

    # quantité
    if qty_target is not None and qty_source is not None:
        merged = merge_quantities(qty_target, unit_target, qty_source, unit_source)
        if merged is not None:
            new_qty, new_unit = merged
            target["quantity"] = new_qty
            target["unit"] = new_unit
        # else: incompatible units, keep target as-is
    elif qty_target is None and qty_source is not None:
        target["quantity"] = qty_source
        # unité
        if unit_target is None and unit_source is not None:
            target["unit"] = unit_source

    # catégorie
    cat_target = _normalize_category(target.get("category"))
    cat_source = _normalize_category(source.get("category"))

    if cat_target == "autres" and cat_source != "autres":
        target["category"] = cat_source

    # transcript
    if not target.get("source_transcript") and source.get("source_transcript"):
        target["source_transcript"] = source.get("source_transcript")


def update_shopping_item(
    item_id: str,
    text: str,
    quantity: int | None = None,
    unit: str | None = None,
    category: str | None = None,
) -> bool:
    if not text:
        return False

    corrected_text = _apply_common_corrections(text)

    if not _is_valid_item(corrected_text):
        return False

    parsed = parse_shopping_item(corrected_text)

    final_text = parsed["text"]
    final_quantity = quantity if quantity is not None else parsed.get("quantity")
    final_unit = unit if unit is not None else parsed.get("unit")
    final_category = _normalize_category(
        category if category is not None else parsed.get("category")
    )

    with _lock:
        data = _load_list("shopping")
        target = None

        for entry in data:
            if entry.get("id") == item_id:
                target = entry
                break

        if target is None:
            return False

        # on met à jour l'item cible
        target["text"] = final_text
        target["quantity"] = final_quantity
        target["unit"] = final_unit
        target["category"] = final_category

        # apprentissage catégorie
        if final_text and final_category != "autres":
            learn_category(final_text, final_category)

        # tentative de fusion avec un autre item compatible
        duplicate = None
        for entry in data:
            if entry.get("id") == item_id:
                continue
            if _shopping_items_can_merge(target, entry):
                duplicate = entry
                break

        if duplicate is not None:
            # on fusionne le duplicate dans target, puis on supprime duplicate
            _merge_shopping_entries(target, duplicate)
            data = [entry for entry in data if entry.get("id") != duplicate.get("id")]

        _save_list("shopping", data)
        return True


def apply_synonym(text: str) -> str:
    data = _load_learning()
    synonyms = data.get("synonyms", {})

    return synonyms.get(text.strip().lower(), text)