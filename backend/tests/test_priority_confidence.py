"""
Tests pour la priorité des actions et le score de confiance combiné règles+LLM.
"""
from __future__ import annotations

from unittest.mock import patch

from app.action_extractor import (
    compute_priority,
    extract_action,
    extract_action_with_fallback,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_llm(intent: str, item: str | None, time_hint: str | None = None):
    """Retourne un patch pour interpret_with_llm renvoyant les valeurs données."""
    return {"intent": intent, "item": item, "time_hint": time_hint}


# ---------------------------------------------------------------------------
# Tests de priorité (via extract_action_with_fallback)
# ---------------------------------------------------------------------------


def test_priority_urgent_appelle_medecin():
    """Mots-clés urgence → priorité haute (1), même via le chemin LLM."""
    llm_response = _mock_llm("todo_add", "médecin")
    with patch("app.action_extractor.interpret_with_llm", return_value=llm_response):
        result = extract_action_with_fallback("urgent, appelle le médecin")
    assert result.get("priority") == 1


def test_priority_idea_add_low():
    """intent idea_add → priorité basse (3)."""
    result = extract_action("j'ai une idée de blague")
    assert result.get("priority") == 3


def test_priority_shopping_normal():
    """Achat sans urgence → priorité normale (2)."""
    result = extract_action("achète du lait")
    assert result.get("priority") == 2


def test_priority_demain_not_high():
    """'demain' seul ne déclenche pas la priorité haute (ce n'est pas 'aujourd'hui')."""
    result = extract_action("il faut acheter du lait demain")
    # priority doit être 2 (normale) car 'demain' n'est pas dans PRIORITY_HIGH_KEYWORDS
    assert result.get("priority") == 2


def test_priority_maintenant_high():
    """'maintenant' → priorité haute (1)."""
    result = extract_action("achète du lait maintenant")
    assert result.get("priority") == 1


def test_priority_un_jour_low():
    """'un jour' dans le texte → priorité basse (3) via compute_priority."""
    priority = compute_priority("il faudrait un jour appeler le plombier", "todo_add")
    assert priority == 3


def test_priority_asap_high():
    """'asap' → priorité haute (1)."""
    with patch("app.action_extractor.interpret_with_llm", return_value=None):
        result = extract_action_with_fallback("il faut appeler le client asap")
    assert result.get("priority") == 1


def test_priority_appointment_today_high():
    """compute_priority pour appointment_add avec time_hint='today' → 1."""
    priority = compute_priority("rdv médecin aujourd'hui", "appointment_add", "today")
    assert priority == 1


def test_priority_appointment_tomorrow_high():
    """compute_priority pour appointment_add avec time_hint='tomorrow' → 1."""
    priority = compute_priority("rdv médecin demain", "appointment_add", "tomorrow")
    assert priority == 1


def test_priority_appointment_no_hint_normal():
    """compute_priority pour appointment_add sans time_hint → 2."""
    priority = compute_priority("prendre rendez-vous chez le dentiste", "appointment_add", None)
    assert priority == 2


# ---------------------------------------------------------------------------
# Tests de confiance combinée
# ---------------------------------------------------------------------------


def test_combined_confidence_llm_agrees():
    """Zone grise + LLM concorde avec les règles → source='combined', boost de confiance.

    "j'ai une idée de blague" → idea_add, confidence=0.65 (zone grise car add_threshold=0.7).
    LLM retourne aussi idea_add → combined = (0.65 + 0.85) / 2 = 0.75.
    """
    llm_response = _mock_llm("idea_add", "blague")
    with patch("app.action_extractor.interpret_with_llm", return_value=llm_response):
        result = extract_action_with_fallback("j'ai une idée de blague")

    assert result.get("source") == "combined"
    expected = (0.65 + 0.85) / 2
    assert abs(result.get("confidence", 0) - expected) < 0.01


def test_combined_confidence_llm_diverges():
    """Zone grise + LLM diverge → source='combined', pénalité doute (rules * 0.8).

    "j'ai une idée de blague" → idea_add, confidence=0.65.
    LLM retourne shopping_add → diverge → 0.65 * 0.8 = 0.52.
    """
    llm_response = _mock_llm("shopping_add", "blague")
    with patch("app.action_extractor.interpret_with_llm", return_value=llm_response):
        result = extract_action_with_fallback("j'ai une idée de blague")

    assert result.get("source") == "combined"
    expected = 0.65 * 0.8
    assert abs(result.get("confidence", 0) - expected) < 0.01


def test_combined_confidence_llm_returns_none():
    """Zone grise + LLM retourne none → pénalité forte (rules * 0.6).

    "j'ai une idée de blague" → idea_add, confidence=0.65.
    LLM retourne none → 0.65 * 0.6 = 0.39.
    """
    llm_response = _mock_llm("none", None)
    with patch("app.action_extractor.interpret_with_llm", return_value=llm_response):
        result = extract_action_with_fallback("j'ai une idée de blague")

    assert result.get("source") == "combined"
    expected = 0.65 * 0.6
    assert abs(result.get("confidence", 0) - expected) < 0.01


def test_high_confidence_no_llm_call():
    """Confiance règles >= add_threshold → pas d'appel LLM, source='rule'."""
    # 'il faut acheter du lait' → shopping_add, confidence=0.80 >= 0.70
    with patch("app.action_extractor.interpret_with_llm") as mock_llm:
        result = extract_action_with_fallback("il faut acheter du lait")
        mock_llm.assert_not_called()

    assert result.get("source") == "rule"
    assert result.get("decision") == "add"


def test_low_confidence_pure_llm_path():
    """Confiance règles <= 0.2 → fallback LLM direct, source='llm'."""
    llm_response = _mock_llm("shopping_add", "café")
    with patch("app.action_extractor.interpret_with_llm", return_value=llm_response):
        result = extract_action_with_fallback("on manque de café au bureau")

    assert result.get("source") == "llm"
    assert result.get("confidence") == 0.65


def test_result_has_priority_field():
    """Tous les résultats de extract_action_with_fallback contiennent 'priority'."""
    with patch("app.action_extractor.interpret_with_llm", return_value=None):
        result = extract_action_with_fallback("achète du lait")
    assert "priority" in result
    assert result["priority"] in (1, 2, 3)
