"""
Post-correction des transcriptions ASR pour les confusions courantes de Whisper en français.
"""
import re

# Mots de remplissage à supprimer
_FILLER_RE = re.compile(
    r'\b(?:e[uh]+|heu+m*|hm+|ben(?=\s)|bah(?=\s))\b\s*',
    re.IGNORECASE
)

_POLITE_RE = re.compile(
    r"s'il (?:vous|te) pla\w+[,\s]*"
    r"|\bsvp\b[,\s]*"
    r"|\bmerci(?: beaucoup)?\b[,\s]*",
    re.IGNORECASE | re.UNICODE,
)

# Corrections déterministes : forme erronée → forme correcte
# Clés en minuscules, appliquées sur le texte normalisé
PHONETIC_FIXES: dict[str, str] = {
    # Confusions temporelles
    "de main": "demain",
    "d'main": "demain",
    # Plombier (confusion classique Whisper FR)
    "pombier": "plombier",
    "fondier": "plombier",
    "plombié": "plombier",
    # Variantes oignon
    "ognon": "oignon",
    "ognons": "oignons",
    # Variantes yaourt
    "yoghourt": "yaourt",
    "yogourt": "yaourt",
    "yoghurt": "yaourt",
    "yogurt": "yaourt",
    # Nombres oraux → chiffres
    "si clémentine": "6 clémentines",
    "six clémentine": "6 clémentines",
    "si citron": "6 citrons",
    "si pomme": "6 pommes",
    "si banane": "6 bananes",
    "deux oeuf": "2 oeufs",
    "deux oeufs": "2 oeufs",
    "trois oeuf": "3 oeufs",
    "trois oeufs": "3 oeufs",
    "quatre oeuf": "4 oeufs",
    # Mots collés/séparés
    "super marché": "supermarché",
    "super-marché": "supermarché",
    "pomme de terres": "pommes de terre",
}

# Noms de professions improbables dans un contexte shopping
# (signale une possible confusion phonétique, abaisse la confiance)
PROFESSION_NOUNS: frozenset[str] = frozenset({
    "pompier", "pompiers",
    "plombier", "plombiers",
    "électricien", "électriciens",
    "mécanicien", "mécaniciens",
    "menuisier", "menuisiers",
    "maçon", "maçons",
    "charpentier", "charpentiers",
    "peintre",       # "peintre" ≠ "pain" mais Whisper peut confondre
    # "avocat" exclu volontairement : c'est aussi un aliment
    # "médecin"/"dentiste" conservés (contexte appointments, pas shopping)
})


def remove_filler_words(text: str) -> str:
    text = _POLITE_RE.sub('', text)
    text = _FILLER_RE.sub('', text)
    return re.sub(r'\s+', ' ', text).strip()


def apply_phonetic_fixes(text: str) -> str:
    lower = text.lower()
    for wrong, correct in PHONETIC_FIXES.items():
        if wrong in lower:
            text = re.sub(re.escape(wrong), correct, text, flags=re.IGNORECASE)
    return text


def is_likely_shopping_mishearing(item: str) -> bool:
    """True si l'item ressemble à un nom de profession improbable en shopping."""
    words = set(item.lower().split())
    return bool(words & PROFESSION_NOUNS)


def correct_transcript(text: str) -> str:
    """Pipeline complet de post-correction ASR."""
    if not text:
        return text
    text = remove_filler_words(text)
    text = apply_phonetic_fixes(text)
    return text.strip()
