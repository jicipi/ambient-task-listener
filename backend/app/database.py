"""
database.py — SQLite backend pour ambient-task-listener.

Toutes les connexions passent par get_db() qui retourne une connexion
avec row_factory = sqlite3.Row.  Le verrou _lock (RLock) est partagé avec
storage.py pour garantir la cohérence des écritures.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ambient.db"

# RLock réentrant : partagé avec storage.py
_lock = threading.RLock()

# Chemin de la base ; peut être surchargé par les tests (":memory:" ou fichier tmp)
_db_path: str = str(DB_PATH)


def set_db_path(path: str) -> None:
    """Surcharge le chemin de la base (utile pour les tests)."""
    global _db_path
    _db_path = path


def get_db_path() -> str:
    return _db_path


def get_db() -> sqlite3.Connection:
    """Retourne une nouvelle connexion avec row_factory configurée."""
    conn = sqlite3.connect(_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Crée les tables si elles n'existent pas encore."""
    # Crée le répertoire parent du fichier DB courant (pas forcément DATA_DIR en test)
    db_file = Path(_db_path)
    if db_file.name != ":memory:":
        db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS items (
                    id              TEXT PRIMARY KEY,
                    list_name       TEXT NOT NULL,
                    text            TEXT NOT NULL,
                    done            INTEGER NOT NULL DEFAULT 0,
                    quantity        REAL,
                    unit            TEXT,
                    category        TEXT,
                    scheduled_date  TEXT,
                    created_at      TEXT,
                    source_transcript TEXT
                );

                CREATE TABLE IF NOT EXISTS pending (
                    id                  TEXT PRIMARY KEY,
                    transcript          TEXT,
                    intent              TEXT,
                    item                TEXT,
                    list_name           TEXT,
                    confidence          REAL,
                    time_hint           TEXT,
                    scheduled_date      TEXT,
                    source              TEXT,
                    decision            TEXT,
                    quantity            REAL,
                    unit                TEXT,
                    created_at          TEXT
                );

                CREATE TABLE IF NOT EXISTS learning_categories (
                    item_text   TEXT PRIMARY KEY,
                    category    TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS learning_synonyms (
                    original    TEXT PRIMARY KEY,
                    normalized  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS category_order (
                    list_name   TEXT NOT NULL,
                    category    TEXT NOT NULL,
                    position    INTEGER NOT NULL,
                    PRIMARY KEY (list_name, category)
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key     TEXT PRIMARY KEY,
                    value   TEXT NOT NULL
                );
            """)
    finally:
        conn.close()
