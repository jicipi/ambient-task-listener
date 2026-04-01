from __future__ import annotations

import uuid
import threading
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from app.cleaning import parse_shopping_item
from app.unit_conversion import units_are_compatible, merge_quantities
from app.date_parser import parse_french_date
import app.database as _db_module


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

# RLock réentrant partagé avec database.py
_lock = _db_module._lock

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

# Initialisation de la base au démarrage du module
_db_module.init_db()


# =========================
# Helpers internes DB
# =========================

def _get_db():
    """Raccourci pour obtenir une connexion depuis le module database."""
    return _db_module.get_db()


# =========================
# Pending
# =========================

def get_pending_items() -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT * FROM pending ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_pending_item(action: dict) -> None:
    list_name = action.get("list")
    item = action.get("item")
    transcript = action.get("transcript")

    parsed = parse_shopping_item(item) if list_name == "shopping" and item else None

    scheduled_date: str | None = None
    intent = action.get("intent")
    if intent == "appointment_add" and transcript:
        scheduled_date = parse_french_date(transcript)

    entry_id = str(uuid.uuid4())
    item_text = parsed["text"] if parsed else item
    quantity = parsed["quantity"] if parsed else None
    unit = parsed["unit"] if parsed else None
    confidence = action.get("confidence")
    time_hint = action.get("time_hint")
    source = action.get("source")
    decision = action.get("decision")
    created_at = datetime.utcnow().isoformat()

    with _lock:
        conn = _get_db()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO pending
                        (id, transcript, intent, item, list_name, confidence,
                         time_hint, scheduled_date, source, decision, quantity,
                         unit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id, transcript, intent, item_text, list_name,
                        confidence, time_hint, scheduled_date, source, decision,
                        quantity, unit, created_at,
                    ),
                )
        finally:
            conn.close()


def reject_pending_item(item_id: str) -> bool:
    with _lock:
        conn = _get_db()
        try:
            with conn:
                cur = conn.execute(
                    "DELETE FROM pending WHERE id = ?", (item_id,)
                )
            return cur.rowcount > 0
        finally:
            conn.close()


def approve_pending_item(
    item_id: str,
    override_text: str | None = None,
    override_list: str | None = None,
    override_quantity: float | None = None,
    override_unit: str | None = None,
    override_scheduled_date: str | None = None,
    priority: int = 2,
) -> bool:
    with _lock:
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM pending WHERE id = ?", (item_id,)
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return False

        target = dict(row)
        list_name = override_list or target.get("list_name")
        item = override_text or target.get("item")
        quantity = override_quantity if override_quantity is not None else target.get("quantity")
        unit = override_unit if override_unit is not None else target.get("unit")
        transcript = target.get("transcript")
        scheduled_date = (
            override_scheduled_date
            if override_scheduled_date is not None
            else target.get("scheduled_date")
        )

        if not list_name or not item:
            return False

        add_item(
            list_name,
            item,
            transcript,
            quantity=quantity,
            unit=unit,
            scheduled_date=scheduled_date,
            priority=priority,
        )

        conn = _get_db()
        try:
            with conn:
                conn.execute("DELETE FROM pending WHERE id = ?", (item_id,))
        finally:
            conn.close()

        return True


# =========================
# Item helpers
# =========================

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
# Learning (catégories / synonymes)
# =========================

def learn_category(item_text: str, category: str) -> None:
    if not item_text or not category:
        return

    key = item_text.strip().lower()
    val = category.strip().lower()

    conn = _get_db()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO learning_categories (item_text, category)
                VALUES (?, ?)
                ON CONFLICT(item_text) DO UPDATE SET category = excluded.category
                """,
                (key, val),
            )
    finally:
        conn.close()


def learn_synonym(original: str, normalized: str) -> None:
    if not original or not normalized:
        return

    key = original.strip().lower()
    val = normalized.strip().lower()

    conn = _get_db()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO learning_synonyms (original, normalized)
                VALUES (?, ?)
                ON CONFLICT(original) DO UPDATE SET normalized = excluded.normalized
                """,
                (key, val),
            )
    finally:
        conn.close()


def apply_synonym(text: str) -> str:
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT normalized FROM learning_synonyms WHERE original = ?",
            (text.strip().lower(),),
        ).fetchone()
    finally:
        conn.close()

    if row:
        return row["normalized"]
    return text


def _get_learned_category(item_text: str) -> str | None:
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT category FROM learning_categories WHERE item_text = ?",
            (item_text.strip().lower(),),
        ).fetchone()
    finally:
        conn.close()

    return row["category"] if row else None


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
    priority: int = 2,
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
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM items WHERE list_name = ?", (list_name,)
            ).fetchall()
            data = [dict(r) for r in rows]
        finally:
            conn.close()

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
                    else:
                        new_qty = existing_quantity + quantity
                        new_unit = existing_unit

                    _update_shopping_fields(
                        existing["id"], final_text, new_qty, new_unit,
                        category or existing.get("category"),
                    )
                    if category:
                        learn_category(final_text, category)
                    return True

                # 2) Enrichissement : ancien sans quantité, nouveau avec quantité,
                # seulement si unités compatibles
                if (
                    quantity is not None
                    and existing_quantity is None
                    and units_compatible
                ):
                    _update_shopping_fields(
                        existing["id"], final_text, quantity, unit,
                        category or existing.get("category"),
                    )
                    if category:
                        learn_category(final_text, category)
                    return True

                # 3) Nouveau sans quantité, ancien avec quantité ET sans unité
                if (
                    quantity is None
                    and existing_quantity is not None
                    and existing_unit is None
                ):
                    _update_shopping_fields(
                        existing["id"], final_text, existing_quantity, existing_unit,
                        category or existing.get("category"),
                    )
                    if category:
                        learn_category(final_text, category)
                    return True

                # 4) Deux items sans quantité
                if quantity is None and existing_quantity is None:
                    _update_shopping_fields(
                        existing["id"], final_text, None, None,
                        category or existing.get("category"),
                    )
                    if category:
                        learn_category(final_text, category)
                    return True

                # 5) Unités incompatibles → ne pas fusionner
                continue

        # For appointments: parse scheduled_date from transcript if not provided
        if list_name == "appointments" and scheduled_date is None and source_transcript:
            scheduled_date = parse_french_date(source_transcript)

        item_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        conn = _get_db()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO items
                        (id, list_name, text, done, quantity, unit, category,
                         scheduled_date, created_at, source_transcript, priority)
                    VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id, list_name, final_text, quantity, unit, category,
                        scheduled_date if list_name == "appointments" else None,
                        created_at, source_transcript, priority,
                    ),
                )
        finally:
            conn.close()

        return True


def _update_shopping_fields(
    item_id: str,
    text: str,
    quantity,
    unit,
    category,
) -> None:
    conn = _get_db()
    try:
        with conn:
            conn.execute(
                """
                UPDATE items
                SET text = ?, quantity = ?, unit = ?, category = ?
                WHERE id = ?
                """,
                (text, quantity, unit, category, item_id),
            )
    finally:
        conn.close()


# =========================
# Public API
# =========================

def _rows_to_list(rows) -> list[dict]:
    result = []
    for r in rows:
        d = dict(r)
        d["done"] = bool(d.get("done", 0))
        result.append(d)
    return result


def get_all_lists() -> dict:
    conn = _get_db()
    try:
        result = {}
        for name in FILES.keys():
            rows = conn.execute(
                "SELECT * FROM items WHERE list_name = ? ORDER BY created_at",
                (name,),
            ).fetchall()
            result[name] = _rows_to_list(rows)
        return result
    finally:
        conn.close()


def get_list(list_name: str) -> list:
    if list_name not in FILES:
        return []

    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM items WHERE list_name = ? ORDER BY created_at",
            (list_name,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def delete_item(list_name: str, item_id: str) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        conn = _get_db()
        try:
            with conn:
                cur = conn.execute(
                    "DELETE FROM items WHERE id = ? AND list_name = ?",
                    (item_id, list_name),
                )
            return cur.rowcount > 0
        finally:
            conn.close()


def update_item_done(list_name: str, item_id: str, done: bool) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        conn = _get_db()
        try:
            with conn:
                cur = conn.execute(
                    "UPDATE items SET done = ? WHERE id = ? AND list_name = ?",
                    (1 if done else 0, item_id, list_name),
                )
            return cur.rowcount > 0
        finally:
            conn.close()


def rename_item(list_name: str, item_id: str, text: str) -> bool:
    if list_name not in FILES or not text:
        return False

    corrected_text = _apply_common_corrections(text)

    if not _is_valid_item(corrected_text):
        return False

    if list_name == "shopping":
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM items WHERE id = ? AND list_name = 'shopping'",
                (item_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return False

        return update_shopping_item(
            item_id=item_id,
            text=corrected_text,
            quantity=None,
            unit=None,
            category=dict(row).get("category"),
        )

    with _lock:
        conn = _get_db()
        try:
            with conn:
                cur = conn.execute(
                    "UPDATE items SET text = ? WHERE id = ? AND list_name = ?",
                    (text.strip(), item_id, list_name),
                )
            return cur.rowcount > 0
        finally:
            conn.close()


def update_item_category(list_name: str, item_id: str, category: str) -> bool:
    if list_name != "shopping" or not category:
        return False

    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ? AND list_name = 'shopping'",
            (item_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False

    entry = dict(row)
    return update_shopping_item(
        item_id=item_id,
        text=entry.get("text", ""),
        quantity=entry.get("quantity"),
        unit=entry.get("unit"),
        category=category,
    )


def update_item_scheduled_date(list_name: str, item_id: str, scheduled_date: str | None) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        conn = _get_db()
        try:
            with conn:
                cur = conn.execute(
                    "UPDATE items SET scheduled_date = ? WHERE id = ? AND list_name = ?",
                    (scheduled_date, item_id, list_name),
                )
            return cur.rowcount > 0
        finally:
            conn.close()


# =========================
# update_shopping_item (full update with merge)
# =========================

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

    if qty_target is not None and qty_source is not None:
        merged = merge_quantities(qty_target, unit_target, qty_source, unit_source)
        if merged is not None:
            new_qty, new_unit = merged
            target["quantity"] = new_qty
            target["unit"] = new_unit
    elif qty_target is None and qty_source is not None:
        target["quantity"] = qty_source
        if unit_target is None and unit_source is not None:
            target["unit"] = unit_source

    cat_target = _normalize_category(target.get("category"))
    cat_source = _normalize_category(source.get("category"))

    if cat_target == "autres" and cat_source != "autres":
        target["category"] = cat_source

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
        conn = _get_db()
        try:
            target_row = conn.execute(
                "SELECT * FROM items WHERE id = ? AND list_name = 'shopping'",
                (item_id,),
            ).fetchone()

            if target_row is None:
                return False

            target = dict(target_row)

            # Met à jour les champs du target
            target["text"] = final_text
            target["quantity"] = final_quantity
            target["unit"] = final_unit
            target["category"] = final_category

            # Apprentissage catégorie
            if final_text and final_category != "autres":
                learn_category(final_text, final_category)

            # Cherche un doublon mergeable
            all_rows = conn.execute(
                "SELECT * FROM items WHERE list_name = 'shopping' AND id != ?",
                (item_id,),
            ).fetchall()
        finally:
            conn.close()

        duplicate = None
        for row in all_rows:
            entry = dict(row)
            if _shopping_items_can_merge(target, entry):
                duplicate = entry
                break

        if duplicate is not None:
            _merge_shopping_entries(target, duplicate)

        conn = _get_db()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE items
                    SET text = ?, quantity = ?, unit = ?, category = ?
                    WHERE id = ?
                    """,
                    (
                        target["text"],
                        target["quantity"],
                        target["unit"],
                        target["category"],
                        item_id,
                    ),
                )

                if duplicate is not None:
                    conn.execute(
                        "DELETE FROM items WHERE id = ?", (duplicate["id"],)
                    )
        finally:
            conn.close()

        return True


# =========================
# Category order
# =========================

def get_category_order(list_name: str) -> list[str]:
    """Retourne les catégories dans l'ordre persisté.
    Les catégories non-listées (présentes dans les items mais absentes de la table)
    sont ajoutées à la fin, triées alphabétiquement.
    """
    conn = _get_db()
    try:
        ordered_rows = conn.execute(
            "SELECT category FROM category_order WHERE list_name = ? ORDER BY position",
            (list_name,),
        ).fetchall()
        ordered = [r["category"] for r in ordered_rows]

        # Récupère toutes les catégories effectivement présentes dans la liste
        cat_rows = conn.execute(
            "SELECT DISTINCT LOWER(COALESCE(category, 'autres')) AS cat FROM items WHERE list_name = ?",
            (list_name,),
        ).fetchall()
        all_cats = {r["cat"] for r in cat_rows}
    finally:
        conn.close()

    ordered_set = set(ordered)
    extra = sorted(c for c in all_cats if c not in ordered_set)
    return ordered + extra


def set_category_order(list_name: str, categories: list[str]) -> bool:
    """Persiste l'ordre des catégories pour une liste donnée."""
    with _lock:
        conn = _get_db()
        try:
            with conn:
                conn.execute(
                    "DELETE FROM category_order WHERE list_name = ?", (list_name,)
                )
                conn.executemany(
                    "INSERT INTO category_order (list_name, category, position) VALUES (?, ?, ?)",
                    [(list_name, cat, pos) for pos, cat in enumerate(categories)],
                )
        finally:
            conn.close()
    return True


# =========================
# Settings
# =========================

def get_setting(key: str, default: str) -> str:
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    finally:
        conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _lock:
        conn = _get_db()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
        finally:
            conn.close()


def reorder_list(list_name: str, ordered_ids: list[str]) -> bool:
    if list_name not in FILES:
        return False

    with _lock:
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM items WHERE list_name = ?", (list_name,)
            ).fetchall()
            items = [dict(r) for r in rows]

            id_to_item = {item["id"]: item for item in items}
            reordered = [id_to_item[i] for i in ordered_ids if i in id_to_item]
            remaining = [item for item in items if item["id"] not in set(ordered_ids)]
            reordered.extend(remaining)

            conn.execute("DELETE FROM items WHERE list_name = ?", (list_name,))
            for item in reordered:
                conn.execute(
                    """INSERT INTO items (id, list_name, text, done, quantity, unit, category, scheduled_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item["id"], item["list_name"], item["text"],
                        item["done"], item["quantity"], item["unit"],
                        item["category"], item["scheduled_date"],
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    return True
