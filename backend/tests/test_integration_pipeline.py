"""
Tests d'intégration bout en bout : texte → extract_action_with_fallback → storage.

Chaque test exerce le pipeline complet :
    texte brut → extract_action_with_fallback → add_item / approve_pending_item
              → vérification dans la DB SQLite temporaire

LLM, catégorie et synonymes sont patchés pour rester déterministes et éviter
tout appel réseau.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixture — DB SQLite isolée + patches LLM
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline(tmp_path):
    """
    Retourne un tuple (extractor, storage) avec :
    - une DB SQLite temporaire (jamais la vraie data/)
    - les patches LLM/catégorie/synonymes actifs
    """
    import app.database as _db
    import app.storage as _storage
    from app.action_extractor import extract_action_with_fallback

    db_file = str(tmp_path / "test_pipeline.db")
    _db.set_db_path(db_file)
    _db.init_db()

    new_files = {
        "shopping":     tmp_path / "shopping.json",
        "todo":         tmp_path / "todo.json",
        "todo_pro":     tmp_path / "todo_pro.json",
        "appointments": tmp_path / "appointments.json",
        "ideas":        tmp_path / "ideas.json",
    }

    with (
        patch.object(_storage, "FILES", new_files),
        patch("app.cleaning.categorize_with_llm", return_value=None),
        patch("app.cleaning.get_learned_category", return_value=None),
        patch("app.cleaning.get_learned_synonym",  return_value=None),
        # Patch both the origin and the imported reference in action_extractor
        patch("app.llm_interpreter.interpret_with_llm", return_value=None),
        patch("app.action_extractor.interpret_with_llm", return_value=None),
    ):
        yield extract_action_with_fallback, _storage

    # Réinitialise la DB vers le vrai fichier après le test
    from pathlib import Path
    _db.set_db_path(str(Path(__file__).resolve().parent.parent / "data" / "ambient.db"))
    _db.init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(pipeline_fixture, text: str) -> dict:
    """Extrait l'action et l'ajoute dans la DB si décision == 'add'."""
    extractor, storage = pipeline_fixture
    result = extractor(text)

    if result.get("decision") == "add":
        list_name = result.get("list")
        item = result.get("item")
        quantity = result.get("quantity") or None
        unit = result.get("unit") or None
        scheduled_date = result.get("scheduled_date") or None
        transcript = result.get("transcript")

        if list_name and item:
            storage.add_item(
                list_name,
                item,
                transcript,
                quantity=quantity,
                unit=unit,
                scheduled_date=scheduled_date,
            )

    return result


# ---------------------------------------------------------------------------
# Test 1 : "ajoute du lait" → shopping_add → 1 item dans shopping
# ---------------------------------------------------------------------------

class TestShoppingAdd:

    def test_lait_added_to_shopping(self, pipeline):
        result = _run(pipeline, "ajoute du lait")
        _, storage = pipeline

        assert result["intent"] == "shopping_add"
        assert result["decision"] == "add"

        items = storage.get_list("shopping")
        assert len(items) == 1
        assert items[0]["text"] == "lait"

    def test_lait_not_duplicated_in_other_lists(self, pipeline):
        _run(pipeline, "ajoute du lait")
        _, storage = pipeline

        # Aucun item dans todo, appointments, etc.
        assert storage.get_list("todo") == []
        assert storage.get_list("appointments") == []


# ---------------------------------------------------------------------------
# Test 2 : "rappelle-moi d'appeler le médecin" → todo_add
# ---------------------------------------------------------------------------

class TestTodoAdd:

    def test_appeler_medecin_todo(self, pipeline):
        # "pense à appeler" matches TODO_PATTERNS rule: r"pense\s+à\s+(.+)"
        result = _run(pipeline, "pense à appeler le médecin")
        _, storage = pipeline

        # Le pipeline règle doit détecter todo_add
        assert result["intent"] == "todo_add"

        items = storage.get_list("todo")
        assert len(items) == 1
        # Le texte stocké doit contenir "médecin"
        assert "médecin" in items[0]["text"]

    def test_appeler_plombier_todo(self, pipeline):
        # "il faut appeler" matches TODO_PATTERNS via LEADERS
        result = _run(pipeline, "il faut appeler le plombier")
        _, storage = pipeline

        assert result["intent"] == "todo_add"
        items = storage.get_list("todo")
        assert len(items) == 1
        assert "plombier" in items[0]["text"]


# ---------------------------------------------------------------------------
# Test 3 : quantité + unité dans le texte ("achète 2 kg de farine")
# ---------------------------------------------------------------------------

class TestShoppingQuantity:

    def test_farine_quantity_kg(self, pipeline):
        # "2 kg de farine" matches pattern: r"^(\d+\s*(?:kg|g|grammes?|...)\s+.+)$"
        result = _run(pipeline, "2 kg de farine")
        _, storage = pipeline

        assert result["intent"] == "shopping_add"

        items = storage.get_list("shopping")
        assert len(items) == 1
        assert items[0]["text"] == "farine"
        assert items[0]["quantity"] == 2
        assert items[0]["unit"] == "kg"

    def test_simple_number_prefix(self, pipeline):
        """'3 yaourts' doit atterrir dans shopping avec qty=3."""
        result = _run(pipeline, "3 yaourts")
        _, storage = pipeline

        assert result["intent"] == "shopping_add"
        items = storage.get_list("shopping")
        assert len(items) == 1
        assert items[0]["quantity"] == 3


# ---------------------------------------------------------------------------
# Test 4 : rendez-vous / appointments + date parsée
# ---------------------------------------------------------------------------

class TestAppointmentAdd:

    def test_caler_reunion_client_todo_pro(self, pipeline):
        # "caler" est dans TODO_PRO_PATTERNS et "client" dans WORK_KEYWORDS
        result = _run(pipeline, "il faut caler une réunion avec le client demain")
        _, storage = pipeline

        assert result["intent"] == "todo_pro_add"
        assert result["decision"] == "add"
        items = storage.get_list("todo_pro")
        assert len(items) == 1

    def test_rendez_vous_dentiste_scheduled_date(self, pipeline):
        result = _run(pipeline, "prendre rendez-vous chez le dentiste demain")
        _, storage = pipeline

        assert result["intent"] == "appointment_add"
        assert result["decision"] == "add"

        items = storage.get_list("appointments")
        assert len(items) == 1
        assert "dentiste" in items[0]["text"]
        # add_item parse la date depuis le transcript quand scheduled_date est None
        # "demain" dans le transcript → scheduled_date non nulle dans la DB
        assert items[0]["scheduled_date"] is not None


# ---------------------------------------------------------------------------
# Test 5 : phrase non pertinente → intent ignore → aucun item ajouté
# ---------------------------------------------------------------------------

class TestIgnoredPhrases:

    def test_oui_merci_ignored(self, pipeline):
        result = _run(pipeline, "oui merci")
        _, storage = pipeline

        assert result["decision"] == "ignore"
        # Aucune liste ne doit avoir d'items
        for list_name in ("shopping", "todo", "todo_pro", "appointments", "ideas"):
            assert storage.get_list(list_name) == []

    def test_bonjour_ignored(self, pipeline):
        result = _run(pipeline, "bonjour")
        _, storage = pipeline

        assert result["decision"] == "ignore"

    def test_phrase_sans_verbe_action_ignored(self, pipeline):
        """Phrase courte sans mot-clé action → ignorée."""
        result = _run(pipeline, "c'est bon")
        _, storage = pipeline

        assert result["decision"] == "ignore"


# ---------------------------------------------------------------------------
# Test 6 : déduplication — même item ajouté 2x → 1 seul item
# ---------------------------------------------------------------------------

class TestDeduplication:

    def test_lait_added_twice_single_entry(self, pipeline):
        _, storage = pipeline

        storage.add_item("shopping", "lait")
        storage.add_item("shopping", "lait")

        items = storage.get_list("shopping")
        assert len(items) == 1

    def test_shopping_same_item_with_quantity_merges(self, pipeline):
        """3 pommes + 2 pommes = 5 pommes (un seul item fusionné)."""
        _, storage = pipeline

        storage.add_item("shopping", "pommes", quantity=3)
        storage.add_item("shopping", "pommes", quantity=2)

        items = storage.get_list("shopping")
        assert len(items) == 1
        assert items[0]["quantity"] == 5


# ---------------------------------------------------------------------------
# Test 7 : approve_pending_item → item dans la liste
# ---------------------------------------------------------------------------

class TestApprovePending:

    def test_approve_pending_adds_to_list(self, pipeline):
        _, storage = pipeline

        action = {
            "transcript": "ajoute du lait",
            "intent": "shopping_add",
            "item": "lait",
            "list": "shopping",
            "confidence": 0.6,
            "time_hint": None,
            "scheduled_date": None,
            "source": "rule",
            "decision": "confirm",
        }
        storage.add_pending_item(action)

        pending = storage.get_pending_items()
        assert len(pending) == 1
        item_id = pending[0]["id"]

        result = storage.approve_pending_item(item_id)
        assert result is True

        # Pending vidé
        assert storage.get_pending_items() == []

        # Item présent dans la liste
        items = storage.get_list("shopping")
        assert len(items) == 1
        assert items[0]["text"] == "lait"

    def test_approve_nonexistent_returns_false(self, pipeline):
        _, storage = pipeline

        result = storage.approve_pending_item("non-existent-id")
        assert result is False


# ---------------------------------------------------------------------------
# Test 8 : reject_pending_item → pending vide, rien dans les listes
# ---------------------------------------------------------------------------

class TestRejectPending:

    def test_reject_pending_clears_pending(self, pipeline):
        _, storage = pipeline

        action = {
            "transcript": "ajoute du beurre",
            "intent": "shopping_add",
            "item": "beurre",
            "list": "shopping",
            "confidence": 0.6,
            "time_hint": None,
            "scheduled_date": None,
            "source": "rule",
            "decision": "confirm",
        }
        storage.add_pending_item(action)

        pending = storage.get_pending_items()
        assert len(pending) == 1
        item_id = pending[0]["id"]

        result = storage.reject_pending_item(item_id)
        assert result is True

        # Pending vidé
        assert storage.get_pending_items() == []

        # Aucun item dans shopping
        assert storage.get_list("shopping") == []

    def test_reject_nonexistent_returns_false(self, pipeline):
        _, storage = pipeline

        result = storage.reject_pending_item("no-such-id")
        assert result is False


# ---------------------------------------------------------------------------
# Test 9 : correction ASR — "du pombier" → "plombier" dans le texte traité
# ---------------------------------------------------------------------------

class TestASRCorrection:

    def test_pombier_corrected_to_plombier_in_transcript(self, pipeline):
        """
        Le pipeline applique correct_transcript() avant l'extraction.
        "pombier" doit être corrigé en "plombier" dans le transcript retourné.
        """
        extractor, _ = pipeline
        result = extractor("pense à appeler du pombier")

        # La correction ASR doit avoir transformé "pombier" → "plombier"
        assert "plombier" in result.get("transcript", "").lower()

    def test_fondier_corrected_to_plombier(self, pipeline):
        extractor, storage = pipeline
        result = extractor("pense à appeler le fondier")

        assert result["intent"] == "todo_add"
        # Le transcript corrigé doit contenir "plombier"
        assert "plombier" in result.get("transcript", "").lower()

        if result.get("decision") == "add":
            storage.add_item(
                result["list"],
                result["item"],
                result["transcript"],
            )
            items = storage.get_list("todo")
            assert len(items) == 1
            assert "plombier" in items[0]["text"]


# ---------------------------------------------------------------------------
# Test 10 : pipeline complet multi-actions (appels successifs indépendants)
# ---------------------------------------------------------------------------

class TestMultipleActions:

    def test_two_shopping_items_then_one_todo(self, pipeline):
        extractor, storage = pipeline

        _run(pipeline, "ajoute du lait")
        _run(pipeline, "ajoute des oeufs")
        _run(pipeline, "pense à appeler le plombier")

        shopping_items = storage.get_list("shopping")
        todo_items = storage.get_list("todo")

        assert len(shopping_items) == 2
        assert len(todo_items) == 1

    def test_idea_add(self, pipeline):
        extractor, storage = pipeline
        result = extractor("j'ai une idée de blague sur les développeurs")

        assert result["intent"] == "idea_add"
        assert result["item"] is not None
        assert "blague" in result["item"]

        # confidence < 0.7 → decision == "confirm" (via pending, pas direct)
        # On vérifie que la décision est cohérente
        assert result["decision"] in ("add", "confirm")


# ---------------------------------------------------------------------------
# Test 11 : pattern "j'ai [event] [jour]" → appointment_add
# ---------------------------------------------------------------------------

class TestAppointmentJai:

    def test_jai_entrainement_lundi(self, pipeline):
        extractor, _ = pipeline
        result = extractor("j'ai entraînement lundi")
        assert result["intent"] == "appointment_add"
        assert result["decision"] in ("add", "confirm")
        assert result["item"] is not None
        assert "entraînement" in result["item"]

    def test_jai_cours_mercredi(self, pipeline):
        extractor, _ = pipeline
        result = extractor("j'ai un cours mercredi")
        assert result["intent"] == "appointment_add"
        assert result["item"] is not None
        assert "cours" in result["item"]

    def test_jai_match_samedi(self, pipeline):
        extractor, _ = pipeline
        result = extractor("j'ai un match samedi")
        assert result["intent"] == "appointment_add"
        assert result["item"] is not None
        assert "match" in result["item"]

    def test_jai_reunion_demain(self, pipeline):
        extractor, _ = pipeline
        result = extractor("j'ai une réunion demain")
        assert result["intent"] == "appointment_add"
        assert result["item"] is not None
        assert "réunion" in result["item"]


# ---------------------------------------------------------------------------
# Test 12 : "[prénom] n'a plus de Y" → shopping_add
# ---------------------------------------------------------------------------

class TestShoppingPrenom:

    def test_helia_na_plus_de_lait(self, pipeline):
        extractor, _ = pipeline
        result = extractor("Hélia n'a plus de lait")
        assert result["intent"] == "shopping_add"
        assert result["item"] is not None
        assert "lait" in result["item"]

    def test_elle_na_plus_de_jus(self, pipeline):
        extractor, _ = pipeline
        result = extractor("elle n'a plus de jus d'orange")
        assert result["intent"] == "shopping_add"
        assert result["item"] is not None
        assert "jus" in result["item"]
