import re
from app.llm_interpreter import categorize_with_llm
from app.user_learning import get_learned_category, get_learned_synonym
from app.asr_corrections import correct_transcript

CATEGORIES = {
    "légumes": [
        "pommes de terre",
        "pomme de terre",
        "patate",
        "patates",
        "carotte",
        "carottes",
        "courgette",
        "courgettes",
        "poireau",
        "poireaux",
        "salade",
        "salades",
        "tomate",
        "tomates",
        "oignon",
        "oignons",
        "ail",
        "brocoli",
        "brocolis",
        "haricot",
        "haricots",
    ],

    "fruits": [
        "pomme",
        "pommes",
        "banane",
        "bananes",
        "orange",
        "oranges",
        "poire",
        "poires",
        "kiwi",
        "kiwis",
        "fraise",
        "fraises",
        "mangue",
        "mangues",
    ],
    "viande": [
        "poulet", "boeuf", "porc", "steak"
    ],
    "poisson": [
        "saumon", "thon", "cabillaud"
    ],
    "produits laitiers": [
        "lait", "fromage", "yaourt", "beurre", "crème", "feta"
    ],
    "épicerie": [
        "pâtes", "riz", "farine", "sucre"
    ],
    "ménager": [
        "lessive", "éponge", "produit vaisselle"
    ],
}


def normalize_transcript(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = correct_transcript(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_item(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\sàâäéèêëîïôöùûüç'-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None

    unit = unit.lower()

    mapping = {
        "kg": "kg",
        "kgs": "kg",
        "kilo": "kg",
        "kilos": "kg",
        "kilogramme": "kg",
        "kilogrammes": "kg",
        "g": "g",
        "gramme": "g",
        "grammes": "g",
        "l": "l",
        "litre": "l",
        "litres": "l",
        "ml": "ml",
        "cl": "cl",
        "boite": "boite",
        "boîte": "boite",
        "boîtes": "boite",
        "boites": "boite",
        "paquet": "paquet",
        "paquets": "paquet",
        "bouteille": "bouteille",
        "bouteilles": "bouteille",
    }

    return mapping.get(unit, unit)


def categorize_item(text: str) -> str:
    text = text.lower().strip()

    learned_category = get_learned_category(text)
    if learned_category:
        return learned_category

    best_category = "autres"
    best_length = 0

    for category, keywords in CATEGORIES.items():
        for word in keywords:
            if word in text and len(word) > best_length:
                best_category = category
                best_length = len(word)

    if best_category == "autres":
        ai_category = categorize_with_llm(text)
        if ai_category:
            return ai_category

    return best_category


def parse_shopping_item(text: str) -> dict:
    text = text.strip().lower()

    word_to_number = {
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
        "sept": 7,
        "huit": 8,
        "neuf": 9,
        "dix": 10,
    }

    unit_map = {
        "kilogrammes": "kg",
        "kilogramme": "kg",
        "kilos": "kg",
        "kilo": "kg",
        "kgs": "kg",
        "kg": "kg",
        "grammes": "g",
        "gramme": "g",
        "g": "g",
        "litres": "l",
        "litre": "l",
        "l": "l",
        "boîtes": "boite",
        "boîte": "boite",
        "boites": "boite",
        "boite": "boite",
        "bouteilles": "bouteille",
        "bouteille": "bouteille",
        "paquets": "paquet",
        "paquet": "paquet",
        "ml": "ml",
        "cl": "cl",
    }

    tokens = text.split()

    quantity = None
    unit = None
    item_tokens = tokens[:]

    # quantité en premier mot (entier, décimal point ou virgule française)
    if item_tokens:
        first = item_tokens[0]
        first_norm = first.replace(',', '.')
        try:
            val = float(first_norm)
            quantity = int(val) if val == int(val) else round(val, 4)
            item_tokens = item_tokens[1:]
        except ValueError:
            if first in word_to_number:
                quantity = word_to_number[first]
                item_tokens = item_tokens[1:]

    # unité en mot suivant
    if item_tokens:
        first = item_tokens[0]
        if first in unit_map:
            unit = unit_map[first]
            item_tokens = item_tokens[1:]

    # retirer un éventuel "de" ou "d'"
    if item_tokens:
        if item_tokens[0] == "de":
            item_tokens = item_tokens[1:]
        elif item_tokens[0].startswith("d'"):
            item_tokens[0] = item_tokens[0][2:]

    item = " ".join(item_tokens).strip()

    # nettoyage commun
    item = item.rstrip(" .,!?:;")
    item = re.sub(r"\s+à\s+la\s+liste$", "", item).strip()
    item = re.sub(r"\s+sur\s+la\s+liste$", "", item).strip()
    item = re.sub(r"^(ce|cet|cette|ces)\s+", "", item).strip()
    item = re.sub(r"^(du|de la|de l'|des)\s+", "", item).strip()

    if not item:
        item = text.strip().lower()

    learned_synonym = get_learned_synonym(item)
    if learned_synonym:
        item = learned_synonym

    return {
        "text": item,
        "quantity": quantity,
        "unit": unit,
        "category": categorize_item(item),
    }