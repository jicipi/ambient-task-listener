from rapidfuzz import process, fuzz


KNOWN_ITEMS = [
    "plombier",
    "dentiste",
    "médecin",
    "banque",
    "restaurant",
    "lait",
    "café",
    "sucre",
    "beurre",
    "pain",
    "piles",
    "papier toilette",
]


SIMILARITY_THRESHOLD = 70


# erreurs fréquentes de transcription
COMMON_MISHEARINGS = {
    "fondier": "plombier",
    "pompier": "plombier",
    "plonbier": "plombier",
    "plombière": "plombier",
}


def correct_item(text: str):

    if not text:
        return text

    text = text.strip().lower()

    # correction directe connue
    if text in COMMON_MISHEARINGS:
        return COMMON_MISHEARINGS[text]

    # fallback fuzzy
    match = process.extractOne(
        text,
        KNOWN_ITEMS,
        scorer=fuzz.WRatio
    )

    if not match:
        return text

    candidate, score, _ = match

    if score >= SIMILARITY_THRESHOLD:
        return candidate

    return text