"""
Parser de dates françaises naturelles.
Aucune dépendance externe : stdlib Python uniquement.
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, date


# Noms des jours en français (lundi = 0, ..., dimanche = 6)
WEEKDAY_NAMES = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

# Noms des mois en français
MONTH_NAMES = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

# Noms des jours pour format_date_fr
WEEKDAY_FR = [
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"
]

MONTH_FR = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

# Pattern compilé une fois pour les mois
_MONTH_PATTERN = "|".join(MONTH_NAMES.keys())

# Regex pour "le 15", "le 15 janvier", "le 15 janvier 2027"
_LE_N_RE = re.compile(
    rf"\ble\s+(\d{{1,2}})(?:\s+({_MONTH_PATTERN}))?(?:\s+(\d{{4}}))?",
)

# Regex pour "dans X jours/semaines/mois"
_DANS_RE = re.compile(r"\bdans\s+(\d+)\s+(jours?|semaines?|mois)\b")


def _next_weekday(ref: date, weekday: int) -> date:
    """
    Retourne la prochaine occurrence du jour de la semaine donné (0=lundi…6=dimanche).
    Si c'est aujourd'hui, retourne la semaine suivante (jamais J+0).
    """
    days_ahead = weekday - ref.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


def _add_months(ref: date, amount: int) -> date:
    """Ajoute `amount` mois à `ref`, en clampant le jour si nécessaire."""
    month = ref.month + amount
    year = ref.year
    while month > 12:
        month -= 12
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(ref.day, last_day)
    return date(year, month, day)


def _try_date(year: int, month: int, day: int) -> date | None:
    """Construit une date, retourne None si invalide."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_french_date(text: str, reference: datetime | None = None) -> str | None:
    """
    Parse une expression de date française et retourne une date ISO (YYYY-MM-DD).
    Retourne None si aucune date trouvée.

    Expressions supportées :
    - "aujourd'hui" / "aujourd hui" → J+0
    - "demain" → J+1
    - "après-demain" / "apres-demain" → J+2
    - "lundi", "mardi", …, "dimanche" → prochain jour (si passé ou aujourd'hui, semaine suivante)
    - "lundi prochain", "mardi prochain", … → semaine suivante de la prochaine occurrence
    - "la semaine prochaine" → lundi de la semaine suivante
    - "le mois prochain" → 1er du mois suivant
    - "dans X jours" / "dans X semaines" / "dans X mois"
    - "le 15" → 15 du mois courant (ou suivant si passé/inexistant)
    - "le 15 janvier" → 15 janvier de l'année courante (ou suivante si passée)
    - "le 15 janvier 2027" → date exacte
    """
    if reference is None:
        reference = datetime.now()

    ref = reference.date()
    normalized = text.strip().lower()
    # Normaliser les apostrophes typographiques
    normalized = normalized.replace("\u2019", "'").replace("\u2018", "'")

    # --- aujourd'hui (avant demain pour éviter faux positifs) ---
    if re.search(r"\baujourd[' ]?hui\b", normalized):
        return ref.isoformat()

    # --- après-demain (avant demain pour éviter match partiel) ---
    if re.search(r"\bap[rè][eè]?s[- ]?demain\b", normalized):
        return (ref + timedelta(days=2)).isoformat()

    # --- demain ---
    if re.search(r"\bdemain\b", normalized):
        return (ref + timedelta(days=1)).isoformat()

    # --- la semaine prochaine ---
    if re.search(r"\bla\s+semaine\s+prochaine\b", normalized):
        # Lundi de la semaine suivante
        days_until_monday = (7 - ref.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        return (ref + timedelta(days=days_until_monday)).isoformat()

    # --- le mois prochain ---
    if re.search(r"\ble\s+mois\s+prochain\b", normalized):
        month = ref.month + 1
        year = ref.year
        if month > 12:
            month = 1
            year += 1
        return date(year, month, 1).isoformat()

    # --- dans X jours / semaines / mois ---
    m = _DANS_RE.search(normalized)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("jour"):
            return (ref + timedelta(days=amount)).isoformat()
        elif unit.startswith("semaine"):
            return (ref + timedelta(weeks=amount)).isoformat()
        else:  # mois
            return _add_months(ref, amount).isoformat()

    # --- lundi prochain, mardi prochain, … ---
    # Doit être testé avant les jours seuls
    for name, weekday_num in WEEKDAY_NAMES.items():
        if re.search(rf"\b{name}\s+prochain\b", normalized):
            # "prochain" = la prochaine occurrence APRÈS la prochaine occurrence normale
            # c'est-à-dire : next_weekday + 7
            base = _next_weekday(ref, weekday_num)
            return (base + timedelta(days=7)).isoformat()

    # --- "le 15 janvier 2027" / "le 15 janvier" / "le 15" ---
    m = _LE_N_RE.search(normalized)
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        year_str = m.group(3)

        month = MONTH_NAMES[month_name] if month_name else ref.month
        year = int(year_str) if year_str else ref.year

        target = _try_date(year, month, day)

        if year_str:
            # Date complète fournie → retourner telle quelle (ou None si invalide)
            return target.isoformat() if target else None

        # Pas d'année fournie
        if target is None:
            # Jour invalide dans ce mois (ex: 31 avril) → essayer le mois suivant
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            target = _try_date(next_year, next_month, day)
            return target.isoformat() if target else None

        if target < ref:
            if not month_name:
                # Pas de mois précisé → mois suivant
                next_month = month + 1
                next_year = year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                target = _try_date(next_year, next_month, day)
                if target is None:
                    # Toujours invalide → encore un mois plus loin
                    next_month += 1
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    target = _try_date(next_year, next_month, day)
            else:
                # Mois précisé mais pas d'année → année suivante
                target = _try_date(year + 1, month, day)

        return target.isoformat() if target else None

    # --- Jours de la semaine seuls : "lundi", "mardi", … ---
    for name, weekday_num in WEEKDAY_NAMES.items():
        if re.search(rf"\b{name}\b", normalized):
            return _next_weekday(ref, weekday_num).isoformat()

    return None


def format_date_fr(iso_date: str, reference: datetime | None = None) -> str:
    """
    Formate une date ISO (YYYY-MM-DD) en français lisible.
    - Aujourd'hui → "Aujourd'hui"
    - Demain → "Demain"
    - Dans ≤ 7 jours → "Lundi 7 avril"
    - Sinon → "15 janvier 2027"
    """
    if reference is None:
        reference = datetime.now()

    ref = reference.date()

    try:
        target = date.fromisoformat(iso_date)
    except ValueError:
        return iso_date

    delta = (target - ref).days

    if delta == 0:
        return "Aujourd'hui"
    if delta == 1:
        return "Demain"
    if 2 <= delta <= 7:
        weekday_name = WEEKDAY_FR[target.weekday()]
        month_name = MONTH_FR[target.month]
        return f"{weekday_name} {target.day} {month_name}"

    month_name = MONTH_FR[target.month]
    return f"{target.day} {month_name} {target.year}"
