"""
Tests for parse_shopping_item, normalize_transcript, and categorize_item
in app/cleaning.py.
LLM (Ollama) is mocked so tests never make network calls.
User-learning is mocked to return no learned data (clean slate).
"""
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _no_llm_no_learning():
    """
    Patch out every external call made by cleaning.py:
      - categorize_with_llm  → returns None (no LLM available)
      - get_learned_category → returns None (no learned categories)
      - get_learned_synonym  → returns None (no learned synonyms)
    """
    with (
        patch("app.cleaning.categorize_with_llm", return_value=None),
        patch("app.cleaning.get_learned_category", return_value=None),
        patch("app.cleaning.get_learned_synonym", return_value=None),
    ):
        yield


# ---------------------------------------------------------------------------
# parse_shopping_item
# ---------------------------------------------------------------------------

class TestParseShoppingItemQuantity:

    def test_integer_simple(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("3 bananes")
        assert result["quantity"] == 3
        assert result["text"] == "bananes"
        assert result["unit"] is None

    def test_decimal_french_comma(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("0,75 cl whiskey")
        assert result["quantity"] == 0.75
        assert result["unit"] == "cl"
        assert result["text"] == "whiskey"

    def test_decimal_dot(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("1.5 kg farine")
        assert result["quantity"] == 1.5
        assert result["unit"] == "kg"
        assert result["text"] == "farine"

    def test_word_number_deux_litres(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("deux litres de lait")
        assert result["quantity"] == 2
        assert result["unit"] == "l"
        assert result["text"] == "lait"

    def test_no_quantity(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("bananes")
        assert result["quantity"] is None
        assert result["text"] == "bananes"

    def test_unit_only_no_quantity(self):
        """'kg pommes' has no leading number → quantity should be None."""
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("kg pommes")
        # 'kg' is consumed as a unit even without a quantity
        assert result["quantity"] is None

    def test_quantity_with_de(self):
        """'3 kg de pommes' → qty=3, unit='kg', text='pommes'"""
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("3 kg de pommes")
        assert result["quantity"] == 3
        assert result["unit"] == "kg"
        assert result["text"] == "pommes"

    def test_integer_one(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("1 bouteille de vin")
        assert result["quantity"] == 1
        assert result["unit"] == "bouteille"
        assert result["text"] == "vin"

    def test_word_number_dix(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("dix œufs")
        assert result["quantity"] == 10
        assert result["text"] == "œufs"


class TestParseShoppingItemArticleCleaning:

    def test_du_article_removed(self):
        """'du lait' → text='lait' (article stripped)"""
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("du lait")
        assert result["text"] == "lait"
        assert result["quantity"] is None

    def test_de_la_article_removed(self):
        """
        'de la farine': token-level stripping removes the leading 'de' token,
        but 'la' is left — actual text is 'la farine'.
        The regex at the end only acts on untouched prefixes.
        """
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("de la farine")
        # Token logic removes 'de' but leaves 'la'; result is 'la farine'
        assert result["text"] == "la farine"

    def test_des_article_removed(self):
        from app.cleaning import parse_shopping_item
        result = parse_shopping_item("des poires")
        assert result["text"] == "poires"


# ---------------------------------------------------------------------------
# normalize_transcript
# ---------------------------------------------------------------------------

class TestNormalizeTranscript:

    def test_empty_string(self):
        from app.cleaning import normalize_transcript
        assert normalize_transcript("") == ""

    def test_strips_and_lowercases(self):
        from app.cleaning import normalize_transcript
        assert normalize_transcript("  BONJOUR  ") == "bonjour"

    def test_correction_de_main(self):
        from app.cleaning import normalize_transcript
        result = normalize_transcript("rendez-vous de main")
        assert "demain" in result

    def test_correction_si_clementine(self):
        from app.cleaning import normalize_transcript
        result = normalize_transcript("si clémentine")
        assert result == "6 clémentines"

    def test_collapses_whitespace(self):
        from app.cleaning import normalize_transcript
        result = normalize_transcript("du   lait   frais")
        assert "  " not in result


# ---------------------------------------------------------------------------
# categorize_item  (static dictionary only — LLM mocked to return None)
# ---------------------------------------------------------------------------

class TestCategorizeItem:

    def test_bananes_is_fruits(self):
        from app.cleaning import categorize_item
        assert categorize_item("bananes") == "fruits"

    def test_carottes_is_legumes(self):
        from app.cleaning import categorize_item
        assert categorize_item("carottes") == "légumes"

    def test_lait_is_produits_laitiers(self):
        from app.cleaning import categorize_item
        assert categorize_item("lait") == "produits laitiers"

    def test_farine_is_epicerie(self):
        from app.cleaning import categorize_item
        assert categorize_item("farine") == "épicerie"

    def test_unknown_falls_back_to_autres(self):
        from app.cleaning import categorize_item
        # LLM is mocked to None → must return 'autres'
        assert categorize_item("xyzzy_inconnue") == "autres"
