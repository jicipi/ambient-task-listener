"""
migrate_json_to_sqlite.py — Migration one-shot des fichiers JSON vers SQLite.

Peut être relancé sans risque : INSERT OR IGNORE ignore les doublons.
Usage:
    cd backend
    source .venv/bin/activate
    python scripts/migrate_json_to_sqlite.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ajoute le répertoire backend au path pour pouvoir importer app.database
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_db, init_db, DATA_DIR  # noqa: E402

LIST_NAMES = ["shopping", "todo", "todo_pro", "appointments", "ideas"]


def migrate_items(conn: object) -> None:
    totals: dict[str, int] = {}

    for list_name in LIST_NAMES:
        path = DATA_DIR / f"{list_name}.json"
        if not path.exists():
            print(f"  [skip] {list_name}.json introuvable")
            continue

        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [erreur] lecture {list_name}.json : {e}")
            continue

        count = 0
        for item in items:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO items
                        (id, list_name, text, done, quantity, unit, category,
                         scheduled_date, created_at, source_transcript)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("id"),
                        list_name,
                        item.get("text") or item.get("item") or "",
                        1 if item.get("done") else 0,
                        item.get("quantity"),
                        item.get("unit"),
                        item.get("category"),
                        item.get("scheduled_date"),
                        item.get("created_at"),
                        item.get("source_transcript"),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"  [erreur] item {item.get('id')} : {e}")

        totals[list_name] = count
        print(f"  {list_name}: {count} item(s) migrés")

    return totals


def migrate_pending(conn: object) -> None:
    path = DATA_DIR / "pending.json"
    if not path.exists():
        print("  [skip] pending.json introuvable")
        return

    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [erreur] lecture pending.json : {e}")
        return

    count = 0
    for item in items:
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO pending
                    (id, transcript, intent, item, list_name, confidence,
                     time_hint, scheduled_date, source, decision, quantity,
                     unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("id"),
                    item.get("transcript"),
                    item.get("intent"),
                    item.get("item"),
                    item.get("list"),
                    item.get("confidence"),
                    item.get("time_hint"),
                    item.get("scheduled_date"),
                    item.get("source"),
                    item.get("decision"),
                    item.get("quantity"),
                    item.get("unit"),
                    item.get("created_at"),
                ),
            )
            count += 1
        except Exception as e:
            print(f"  [erreur] pending item {item.get('id')} : {e}")

    print(f"  pending: {count} item(s) migrés")


def migrate_learning(conn: object) -> None:
    path = DATA_DIR / "user_learning.json"
    if not path.exists():
        print("  [skip] user_learning.json introuvable")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [erreur] lecture user_learning.json : {e}")
        return

    cats = data.get("categories", {})
    syns = data.get("synonyms", {})

    cat_count = 0
    for item_text, category in cats.items():
        try:
            conn.execute(
                "INSERT OR IGNORE INTO learning_categories (item_text, category) VALUES (?, ?)",
                (item_text, category),
            )
            cat_count += 1
        except Exception as e:
            print(f"  [erreur] catégorie '{item_text}' : {e}")

    syn_count = 0
    for original, normalized in syns.items():
        try:
            conn.execute(
                "INSERT OR IGNORE INTO learning_synonyms (original, normalized) VALUES (?, ?)",
                (original, normalized),
            )
            syn_count += 1
        except Exception as e:
            print(f"  [erreur] synonyme '{original}' : {e}")

    print(f"  learning_categories: {cat_count} entrée(s) migrée(s)")
    print(f"  learning_synonyms: {syn_count} entrée(s) migrée(s)")


def main() -> None:
    print("=== Migration JSON → SQLite ===")
    print(f"Base cible : {DATA_DIR / 'ambient.db'}")
    print()

    init_db()
    conn = get_db()

    try:
        with conn:
            print("--- Items ---")
            migrate_items(conn)
            print()
            print("--- Pending ---")
            migrate_pending(conn)
            print()
            print("--- Learning ---")
            migrate_learning(conn)
    finally:
        conn.close()

    print()
    print("Migration terminée.")


if __name__ == "__main__":
    main()
