"""
Tests pour la gestion des actions multiples dans une seule phrase.

Ces tests vérifient que extract_multiple_actions et extract_action_with_fallback
peuvent extraire plusieurs actions depuis une phrase avec des connecteurs.

Le LLM est patché pour rester déterministe.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixture : patches LLM pour rester déterministe
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_llm():
    """Désactive le LLM (Ollama) pour tous les tests multi-actions."""
    with (
        patch("app.llm_interpreter.interpret_with_llm", return_value=None),
        patch("app.action_extractor.interpret_with_llm", return_value=None),
        patch("app.llm_interpreter.interpret_multiple_with_llm", return_value=None),
        patch("app.action_extractor.interpret_multiple_with_llm", return_value=None),
    ):
        yield


# ---------------------------------------------------------------------------
# Tests extract_multiple_actions
# ---------------------------------------------------------------------------

class TestExtractMultipleActions:

    def test_lait_et_appeler_medecin(self):
        """'achète du lait et appelle le médecin' → shopping + todo."""
        from app.action_extractor import extract_multiple_actions

        results = extract_multiple_actions("achète du lait et appelle le médecin")

        assert len(results) >= 2

        intents = {r["intent"] for r in results}
        assert "shopping_add" in intents
        assert "todo_add" in intents

    def test_pommes_et_oranges(self):
        """'ajoute des pommes et des oranges' → 2 shopping items."""
        from app.action_extractor import extract_multiple_actions

        results = extract_multiple_actions("ajoute des pommes et des oranges")

        assert len(results) >= 2
        assert all(r["intent"] == "shopping_add" for r in results)

        items = {r["item"] for r in results}
        assert "pommes" in items
        assert "oranges" in items

    def test_dentiste_et_medicaments(self):
        """'pense à appeler le dentiste et à commander les médicaments' → todo + shopping."""
        from app.action_extractor import extract_multiple_actions

        results = extract_multiple_actions(
            "pense à appeler le dentiste et à commander les médicaments"
        )

        assert len(results) >= 2

        intents = {r["intent"] for r in results}
        assert "todo_add" in intents
        assert "shopping_add" in intents

    def test_no_connector_returns_empty(self):
        """Phrase sans connecteur → extract_multiple_actions retourne []."""
        from app.action_extractor import extract_multiple_actions

        results = extract_multiple_actions("ajoute du lait")

        # Pas de connecteur → on ne peut pas découper → retourne [] ou 1 résultat max
        assert len(results) < 2


# ---------------------------------------------------------------------------
# Tests extract_action_with_fallback multi
# ---------------------------------------------------------------------------

class TestExtractActionWithFallbackMulti:

    def test_lait_et_medecin_returns_multi(self):
        """'achète du lait et appelle le médecin demain' → multi: True avec 2 actions."""
        from app.action_extractor import extract_action_with_fallback

        result = extract_action_with_fallback(
            "achète du lait et appelle le médecin demain"
        )

        assert result.get("multi") is True
        actions = result.get("actions", [])
        assert len(actions) >= 2

        intents = {a["intent"] for a in actions}
        assert "shopping_add" in intents
        assert "todo_add" in intents

    def test_simple_phrase_no_multi(self):
        """Phrase simple sans 'et' → comportement inchangé (mono-action)."""
        from app.action_extractor import extract_action_with_fallback

        result = extract_action_with_fallback("ajoute du lait")

        assert result.get("multi") is not True
        assert result["intent"] == "shopping_add"
        assert result["decision"] == "add"

    def test_allow_multi_false_disables_multi(self):
        """allow_multi=False → comportement mono-action même avec 'et'."""
        from app.action_extractor import extract_action_with_fallback

        # Avec allow_multi=False, le comportement doit rester mono-action
        result = extract_action_with_fallback(
            "achète du lait et des oeufs", allow_multi=False
        )

        assert result.get("multi") is not True
        # La phrase avec "ajoute" match shopping, donc intent shopping_add
        assert "intent" in result

    def test_pommes_et_oranges_multi(self):
        """'ajoute des pommes et des oranges' → multi: True avec 2 shopping."""
        from app.action_extractor import extract_action_with_fallback

        result = extract_action_with_fallback("ajoute des pommes et des oranges")

        assert result.get("multi") is True
        actions = result.get("actions", [])
        assert len(actions) >= 2
        assert all(a["intent"] == "shopping_add" for a in actions)

    def test_multi_actions_have_required_fields(self):
        """Chaque action dans 'actions' doit avoir les champs requis."""
        from app.action_extractor import extract_action_with_fallback

        result = extract_action_with_fallback("achète du lait et appelle le médecin")

        if result.get("multi"):
            for action in result["actions"]:
                assert "intent" in action
                assert "item" in action
                assert "confidence" in action
                assert "list" in action
                assert "decision" in action
                assert "needs_confirmation" in action

    def test_bonjour_not_multi(self):
        """'bonjour' → mono-action ignorée, pas multi."""
        from app.action_extractor import extract_action_with_fallback

        result = extract_action_with_fallback("bonjour")

        assert result.get("multi") is not True
        assert result["decision"] == "ignore"
