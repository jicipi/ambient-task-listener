"""Tests for the ASR post-correction module."""
import pytest
from app.asr_corrections import (
    remove_filler_words,
    apply_phonetic_fixes,
    is_likely_shopping_mishearing,
    correct_transcript,
    apply_user_names_fixes,
)


# ---------------------------------------------------------------------------
# remove_filler_words
# ---------------------------------------------------------------------------

class TestRemoveFillerWords:
    def test_removes_euh(self):
        assert remove_filler_words("euh j'ai besoin de lait") == "j'ai besoin de lait"

    def test_removes_euh_long(self):
        assert remove_filler_words("euuuh du pain") == "du pain"

    def test_removes_hm(self):
        assert remove_filler_words("hm du beurre") == "du beurre"

    def test_removes_hmm(self):
        assert remove_filler_words("hmm il faut acheter du riz") == "il faut acheter du riz"

    def test_removes_sil_vous_plait(self):
        assert remove_filler_words("achète du pain s'il vous plaît") == "achète du pain"

    def test_removes_sil_te_plait(self):
        assert remove_filler_words("ajoute du lait s'il te plaît") == "ajoute du lait"

    def test_removes_svp(self):
        assert remove_filler_words("rajoute des oeufs svp") == "rajoute des oeufs"

    def test_removes_merci(self):
        assert remove_filler_words("il faut du café merci") == "il faut du café"

    def test_removes_merci_beaucoup(self):
        assert remove_filler_words("achète du lait merci beaucoup") == "achète du lait"

    def test_no_filler_unchanged(self):
        assert remove_filler_words("il faut acheter du lait") == "il faut acheter du lait"

    def test_empty_string(self):
        assert remove_filler_words("") == ""

    def test_only_filler_returns_empty(self):
        result = remove_filler_words("euh")
        assert result == ""

    def test_case_insensitive_filler(self):
        assert remove_filler_words("EUH du pain") == "du pain"


# ---------------------------------------------------------------------------
# apply_phonetic_fixes
# ---------------------------------------------------------------------------

class TestApplyPhoneticFixes:
    def test_pombier_to_plombier(self):
        assert apply_phonetic_fixes("appeler le pombier") == "appeler le plombier"

    def test_fondier_to_plombier(self):
        assert apply_phonetic_fixes("le fondier est là") == "le plombier est là"

    def test_de_main_to_demain(self):
        assert apply_phonetic_fixes("rendez-vous de main") == "rendez-vous demain"

    def test_ognon_to_oignon(self):
        assert apply_phonetic_fixes("acheter des ognons") == "acheter des oignons"

    def test_ognon_singular(self):
        assert apply_phonetic_fixes("un ognon") == "un oignon"

    def test_yoghourt_to_yaourt(self):
        assert apply_phonetic_fixes("du yoghourt") == "du yaourt"

    def test_yogourt_to_yaourt(self):
        assert apply_phonetic_fixes("du yogourt") == "du yaourt"

    def test_yoghurt_to_yaourt(self):
        assert apply_phonetic_fixes("yoghurt nature") == "yaourt nature"

    def test_yogurt_to_yaourt(self):
        assert apply_phonetic_fixes("yogurt") == "yaourt"

    def test_si_clementine_to_6(self):
        assert apply_phonetic_fixes("si clémentine") == "6 clémentines"

    def test_six_clementine_to_6(self):
        assert apply_phonetic_fixes("six clémentine") == "6 clémentines"

    def test_super_marche_collé(self):
        assert apply_phonetic_fixes("au super marché") == "au supermarché"

    def test_pomme_de_terres_plural(self):
        assert apply_phonetic_fixes("pomme de terres") == "pommes de terre"

    def test_case_insensitive(self):
        result = apply_phonetic_fixes("POMBIER")
        assert result.lower() == "plombier"

    def test_no_fix_needed(self):
        assert apply_phonetic_fixes("du lait et du pain") == "du lait et du pain"


# ---------------------------------------------------------------------------
# is_likely_shopping_mishearing
# ---------------------------------------------------------------------------

class TestIsLikelyShoppingMishearing:
    def test_pompier_is_mishearing(self):
        assert is_likely_shopping_mishearing("pompier") is True

    def test_pompiers_plural_is_mishearing(self):
        assert is_likely_shopping_mishearing("pompiers") is True

    def test_plombier_is_mishearing(self):
        assert is_likely_shopping_mishearing("plombier") is True

    def test_electricien_is_mishearing(self):
        assert is_likely_shopping_mishearing("électricien") is True

    def test_peintre_is_mishearing(self):
        assert is_likely_shopping_mishearing("peintre") is True

    def test_avocat_is_not_mishearing(self):
        # avocat is also a food
        assert is_likely_shopping_mishearing("avocat") is False

    def test_pomme_is_not_mishearing(self):
        assert is_likely_shopping_mishearing("pomme") is False

    def test_lait_is_not_mishearing(self):
        assert is_likely_shopping_mishearing("lait") is False

    def test_empty_string(self):
        assert is_likely_shopping_mishearing("") is False

    def test_phrase_with_profession(self):
        assert is_likely_shopping_mishearing("2 pompiers") is True


# ---------------------------------------------------------------------------
# correct_transcript (pipeline complet)
# ---------------------------------------------------------------------------

class TestCorrectTranscript:
    def test_filler_then_fix(self):
        result = correct_transcript("euh acheter du pombier de main")
        assert "euh" not in result
        assert "plombier" in result
        assert "demain" in result

    def test_empty_returns_empty(self):
        assert correct_transcript("") == ""

    def test_no_change_needed(self):
        text = "il faut acheter du lait"
        assert correct_transcript(text) == text

    def test_strips_whitespace(self):
        result = correct_transcript("  du pain  ")
        assert result == "du pain"

    def test_svp_removed_and_fix_applied(self):
        result = correct_transcript("rajoute des ognons svp")
        assert "svp" not in result
        assert "oignon" in result

    def test_uppercase_preserved_after_fix(self):
        # apply_phonetic_fixes is case-insensitive but preserves original case for unmatched parts
        result = correct_transcript("Du YOGHOURT nature")
        assert "yaourt" in result.lower()


# ---------------------------------------------------------------------------
# Nouvelles corrections — session réelle
# ---------------------------------------------------------------------------

class TestNewPhoneticFixes:

    # Rhum
    def test_rom_to_rhum(self):
        assert apply_phonetic_fixes("du rom") == "du rhum"

    # Yaourt grec — variantes "yard-ot"
    def test_yard_ot_grec_hyphen(self):
        assert apply_phonetic_fixes("yard-ot-grec") == "yaourt grec"

    def test_yard_ot_grec_space(self):
        assert apply_phonetic_fixes("yard ot grec") == "yaourt grec"

    def test_yard_ot_hyphen(self):
        assert apply_phonetic_fixes("yard-ot") == "yaourt"

    def test_yardot(self):
        assert apply_phonetic_fixes("yardot") == "yaourt"

    # Céréales
    def test_ses_reels(self):
        assert apply_phonetic_fixes("ses réels") == "céréales"

    def test_ses_reel_singular(self):
        assert apply_phonetic_fixes("ses réel") == "céréales"

    def test_ces_reels(self):
        assert apply_phonetic_fixes("ces réels") == "céréales"

    # Adoucissant
    def test_la_doucissante(self):
        assert apply_phonetic_fixes("la doucissante") == "l'adoucissant"

    def test_de_la_doucissante(self):
        assert apply_phonetic_fixes("de la doucissante") == "de l'adoucissant"

    def test_doucissante_alone(self):
        assert apply_phonetic_fixes("doucissante") == "adoucissant"


# ---------------------------------------------------------------------------
# Corrections prénoms — USER_NAMES_FIXES (contextuelles)
# ---------------------------------------------------------------------------

class TestUserNamesFixes:

    def test_elias_after_emmener(self):
        result = apply_user_names_fixes("il faut emmener elias à l'école")
        assert "hélia" in result.lower()

    def test_elia_after_avec(self):
        result = apply_user_names_fixes("avec elia au parc")
        assert "hélia" in result.lower()

    def test_lian_after_pour(self):
        result = apply_user_names_fixes("acheter pour lian")
        # "pour lian" sans mot suivant déclencheur → pas de contexte "suivi de"
        # mais "pour" est un mot précédent → corrigé
        assert "hélia" in result.lower()

    def test_elias_before_na(self):
        result = apply_user_names_fixes("elias n'a plus de lait")
        assert "hélia" in result.lower()

    def test_elias_before_a_besoin(self):
        result = apply_user_names_fixes("elias a besoin de chaussures")
        assert "hélia" in result.lower()

    def test_elias_without_context_not_corrected(self):
        # "elias" seul, sans contexte déclencheur → ne doit PAS être corrigé
        result = apply_user_names_fixes("j'ai appelé elias hier")
        assert "hélia" not in result.lower()

    def test_correct_transcript_applies_names(self):
        result = correct_transcript("emmener elias à l'école")
        assert "hélia" in result.lower()
