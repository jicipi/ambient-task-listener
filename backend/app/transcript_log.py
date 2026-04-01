"""Logging des transcripts et décisions pour apprentissage supervisé futur.

Chaque utterance est enregistrée dans data/transcripts.jsonl (une ligne JSON par entrée).
Le fichier est append-only pour les nouveaux logs, et réécrit uniquement lors des corrections.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

_LOCK = threading.RLock()
_LOG_FILE = Path(__file__).parent.parent / "data" / "transcripts.jsonl"


def _ensure_file() -> None:
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _LOG_FILE.exists():
        _LOG_FILE.touch()


def log_transcript(transcript: str, actions: list[dict]) -> str:
    """Enregistre un transcript et ses actions dans le fichier JSONL.

    Retourne l'id de l'entrée créée.
    """
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "transcript": transcript,
        "actions": [
            {
                "intent": a.get("intent", "unknown"),
                "item": a.get("item"),
                "list": a.get("list"),
                "decision": a.get("decision"),
                "confidence": a.get("confidence"),
                "source": a.get("source"),
                "priority": a.get("priority"),
                "corrected": None,
            }
            for a in actions
        ],
    }

    with _LOCK:
        _ensure_file()
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry_id


def get_recent_logs(n: int = 50) -> list[dict]:
    """Retourne les N dernières entrées du fichier JSONL."""
    with _LOCK:
        _ensure_file()
        lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()

    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return entries[-n:] if len(entries) > n else entries


def correct_log_entry(log_id: str, action_index: int, correction: dict) -> bool:
    """Ajoute une correction à une entrée existante.

    Réécrit le fichier entier (fichier petit en pratique).
    Retourne True si l'entrée a été trouvée et corrigée, False sinon.
    """
    with _LOCK:
        _ensure_file()
        lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()

        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        found = False
        for entry in entries:
            if entry.get("id") == log_id:
                actions = entry.get("actions", [])
                if 0 <= action_index < len(actions):
                    actions[action_index]["corrected"] = correction
                    found = True
                break

        if found:
            with _LOG_FILE.open("w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return found
