"""
Tests for date_parser.py.

Date de référence fixe : 2026-04-01 (mercredi).
"""
from __future__ import annotations

import pytest
from datetime import datetime

from app.date_parser import parse_french_date, format_date_fr

# Reference fixe : mercredi 1er avril 2026
REF = datetime(2026, 4, 1)


def parse(text: str) -> str | None:
    return parse_french_date(text, reference=REF)


# ---------------------------------------------------------------------------
# parse_french_date
# ---------------------------------------------------------------------------

class TestAujourdhui:
    def test_apostrophe(self):
        assert parse("aujourd'hui") == "2026-04-01"

    def test_sans_apostrophe(self):
        assert parse("aujourd hui") == "2026-04-01"

    def test_dans_phrase(self):
        assert parse("rendez-vous aujourd'hui") == "2026-04-01"


class TestDemain:
    def test_simple(self):
        assert parse("demain") == "2026-04-02"

    def test_dans_phrase(self):
        assert parse("prendre rdv demain matin") == "2026-04-02"


class TestApresdemain:
    def test_tiret(self):
        assert parse("après-demain") == "2026-04-03"

    def test_sans_tiret(self):
        assert parse("après demain") == "2026-04-03"

    def test_sans_accent(self):
        assert parse("apres-demain") == "2026-04-03"


class TestJoursSemaine:
    """
    Référence : mercredi 1er avril 2026.
    "lundi" doit retourner le lundi suivant (= 6 avril, soit dans 5 jours).
    Les jours déjà passés cette semaine (lundi, mardi) → semaine suivante.
    Le jour courant (mercredi) → mercredi prochain (8 avril).
    """
    def test_lundi(self):
        # Lundi passé cette semaine → lundi prochain = 6 avril
        assert parse("lundi") == "2026-04-06"

    def test_mardi(self):
        # Mardi passé cette semaine → mardi prochain = 7 avril
        assert parse("mardi") == "2026-04-07"

    def test_mercredi(self):
        # Mercredi = aujourd'hui → mercredi PROCHAIN = 8 avril
        assert parse("mercredi") == "2026-04-08"

    def test_jeudi(self):
        # Jeudi prochain = 2 avril
        assert parse("jeudi") == "2026-04-02"

    def test_vendredi(self):
        assert parse("vendredi") == "2026-04-03"

    def test_samedi(self):
        assert parse("samedi") == "2026-04-04"

    def test_dimanche(self):
        assert parse("dimanche") == "2026-04-05"


class TestJourProchain:
    """
    "X prochain" = la semaine suivante forcément (au moins +7 jours).
    """
    def test_lundi_prochain(self):
        # Lundi prochain = 13 avril (2 semaines après lundi passé)
        assert parse("lundi prochain") == "2026-04-13"

    def test_jeudi_prochain(self):
        # Jeudi prochain = le jeudi de la semaine suivante = 9 avril
        assert parse("jeudi prochain") == "2026-04-09"

    def test_mercredi_prochain(self):
        # Mercredi prochain = 15 avril
        assert parse("mercredi prochain") == "2026-04-15"


class TestSemaineProchaine:
    def test_la_semaine_prochaine(self):
        # Lundi de la semaine suivante depuis mercredi 1er avril
        # Semaine courante commence le lundi 30 mars ; semaine suivante = lundi 6 avril
        assert parse("la semaine prochaine") == "2026-04-06"


class TestMoisProchain:
    def test_le_mois_prochain(self):
        # 1er mai 2026
        assert parse("le mois prochain") == "2026-05-01"

    def test_decembre_vers_janvier(self):
        ref_dec = datetime(2026, 12, 15)
        assert parse_french_date("le mois prochain", reference=ref_dec) == "2027-01-01"


class TestDansNJours:
    def test_dans_3_jours(self):
        assert parse("dans 3 jours") == "2026-04-04"

    def test_dans_1_jour(self):
        assert parse("dans 1 jour") == "2026-04-02"


class TestDansNSemaines:
    def test_dans_2_semaines(self):
        assert parse("dans 2 semaines") == "2026-04-15"

    def test_dans_1_semaine(self):
        assert parse("dans 1 semaine") == "2026-04-08"


class TestDansNMois:
    def test_dans_1_mois(self):
        assert parse("dans 1 mois") == "2026-05-01"

    def test_dans_3_mois(self):
        assert parse("dans 3 mois") == "2026-07-01"

    def test_dans_mois_depasse_annee(self):
        ref = datetime(2026, 11, 15)
        assert parse_french_date("dans 3 mois", reference=ref) == "2027-02-15"


class TestLeN:
    def test_le_15_futur(self):
        # 15 avril 2026 (dans le futur)
        assert parse("le 15") == "2026-04-15"

    def test_le_1_passe(self):
        # 1er avril 2026 = aujourd'hui, mais "le 1" est la ref elle-même
        # Comme target == ref, c'est pas passé mais égal → date du même mois
        assert parse("le 1") == "2026-04-01"

    def test_le_31_mois_suivant(self):
        # 31 mars est passé → 31 mai 2026 (avril n'a pas de 31)
        # En fait le 31 en avril n'existe pas → ValueError → None
        result = parse("le 31")
        # Avril 2026 n'a pas de 31 → on avance au mois suivant = mai 31
        assert result == "2026-05-31"

    def test_le_15_janvier(self):
        # 15 janvier 2026 est passé → 15 janvier 2027
        assert parse("le 15 janvier") == "2027-01-15"

    def test_le_20_mai(self):
        # 20 mai 2026 est dans le futur
        assert parse("le 20 mai") == "2026-05-20"

    def test_le_15_janvier_2027(self):
        # Date complète avec année
        assert parse("le 15 janvier 2027") == "2027-01-15"

    def test_le_1_decembre_2026(self):
        assert parse("le 1 décembre 2026") == "2026-12-01"


class TestNonReconnu:
    def test_texte_vide(self):
        assert parse("") is None

    def test_texte_sans_date(self):
        assert parse("rendez-vous chez le médecin") is None

    def test_texte_aleatoire(self):
        assert parse("bonjour tout le monde") is None


# ---------------------------------------------------------------------------
# format_date_fr
# ---------------------------------------------------------------------------

class TestFormatDateFr:
    def test_aujourd_hui(self):
        assert format_date_fr("2026-04-01", reference=REF) == "Aujourd'hui"

    def test_demain(self):
        assert format_date_fr("2026-04-02", reference=REF) == "Demain"

    def test_dans_3_jours(self):
        # 4 avril = samedi
        result = format_date_fr("2026-04-04", reference=REF)
        assert result == "Samedi 4 avril"

    def test_dans_7_jours(self):
        # 8 avril = mercredi
        result = format_date_fr("2026-04-08", reference=REF)
        assert result == "Mercredi 8 avril"

    def test_au_dela_7_jours(self):
        result = format_date_fr("2026-04-15", reference=REF)
        assert result == "15 avril 2026"

    def test_autre_annee(self):
        result = format_date_fr("2027-01-15", reference=REF)
        assert result == "15 janvier 2027"

    def test_date_invalide(self):
        # Doit retourner la chaîne telle quelle si invalide
        result = format_date_fr("not-a-date", reference=REF)
        assert result == "not-a-date"
