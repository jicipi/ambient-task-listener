import re


STOP_WORDS = [
    "du",
    "de",
    "des",
    "le",
    "la",
    "les",
    "un",
    "une",
    "à",
    "au",
    "aux",
    "chez",
]


def clean_item(text: str) -> str:

    if not text:
        return text

    text = text.lower().strip()

    # retirer ponctuation
    text = re.sub(r"[.,!?]", "", text)

    words = text.split()

    # retirer stop words au début
    while words and words[0] in STOP_WORDS:
        words.pop(0)

    text = " ".join(words)

    corrections = {
        "plombier de main": "plombier",
        "plombier demain": "plombier",
    }

    if text in corrections:
        text = corrections[text]

    return text


def normalize_transcript(text: str) -> str:

    if not text:
        return text

    text = text.lower()

    replacements = [
        ("de main matin", "demain matin"),
        ("de main soir", "demain soir"),
        ("de main", "demain"),
    ]

    for wrong, correct in replacements:
        text = text.replace(wrong, correct)

    return text