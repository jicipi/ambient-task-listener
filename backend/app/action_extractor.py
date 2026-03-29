from __future__ import annotations

import re
from typing import Any

from app.llm_interpreter import interpret_with_llm


NEGATION_PATTERNS = [
    r"\bne\s+faut\s+pas\b",
    r"\bil\s+ne\s+faut\s+plus\b",
    r"\bpas\s+besoin\s+de\b",
]

TIME_HINTS = {
    "demain": "tomorrow",
    "ce soir": "this_evening",
    "ce week-end": "this_weekend",
    "samedi": "saturday",
    "dimanche": "sunday",
    "lundi": "monday",
    "mardi": "tuesday",
    "mercredi": "wednesday",
    "jeudi": "thursday",
    "vendredi": "friday",
}

TIME_SUFFIXES = [
    " demain",
    " ce soir",
    " ce week-end",
    " samedi",
    " dimanche",
    " lundi",
    " mardi",
    " mercredi",
    " jeudi",
    " vendredi",
]

WORK_KEYWORDS = [
    "demande",
    "client",
    "devis",
    "réunion",
    "formation",
    "atelier",
    "présentation",
    "projet",
    "session",
    "support",
    "contrat",
    "livrable",
    "comité",
]

LEADERS = (
    r"(?:il faut|il faudrait|il fallait|faudra|faut|pense à|pensez à|"
    r"n'oublie pas de|n’oublie pas de|rajoute|rajoutez|ajoute|ajoutez)"
)

PERSONAL_LEADERS = (
    r"(?:il faut que |il faudrait que |il fallait que |"
    r"je dois |je devrais |je vais devoir )"
)

SHOPPING_PATTERNS = [
    r"il\s+faut\s+que\s+j['’]ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"il\s+faut\s+que\s+je\s+ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"il\s+faudrait\s+que\s+j['’]ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"il\s+faudrait\s+que\s+je\s+ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"il\s+fallait\s+que\s+j['’]ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"il\s+fallait\s+que\s+je\s+ach[eè]te?\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"je\s+dois\s+achet\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"je\s+devrais\s+achet\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"je\s+vais\s+devoir\s+achet\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    rf"(?:{LEADERS})?\s*(?:achet\w*|rachet\w*|command\w*|ajout\w*|rajout\w*|prendre)\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"on\s+n[' ]?a\s+plus\s+de\s+(.+)",
    r"il\s+nous\s+faut\s+(.+)",
    r"rajoute\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"ajoute\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"^(\d+\s*(?:kg|g|grammes?|l|litres?|ml|cl|paquets?|packs?|bouteilles?)\s+.+)$",
    r"^(\d+\s+.+)$",
]

TODO_PATTERNS = [
    rf"(?:{LEADERS})\s*appeler\s+(.+)",
    rf"(?:{LEADERS})\s*envoyer\s+(.+)",
    rf"(?:{LEADERS})\s*faire\s+(.+)",
    rf"(?:{LEADERS})\s*penser\s+à\s+(.+)",
    rf"(?:{LEADERS})\s*prévoir\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})\s*appeler\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})\s*envoyer\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})\s*faire\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})\s*penser\s+à\s+(.+)",
    r"pense\s+à\s+(.+)",
    r"n['’]oublie\s+pas\s+de\s+(.+)",
]

APPOINTMENT_PATTERNS = [
    rf"(?:{LEADERS})?\s*prendre\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
    r"(?:prends|prenez)\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
    rf"(?:{LEADERS})\s*réserver\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})(?:prenne|prendre)\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
]

IDEA_PATTERNS = [
    r"(?:j'ai|jai)\s+une\s+idée\s+(?:de|pour)\s+(.+)",
    r"(?:tiens|au fait)?\s*(?:j'ai|jai)\s+une\s+idée\s+(.+)",
    r"(?:note|garde|ajoute)\s+une\s+idée\s+(?:de|pour)\s+(.+)",
    r"(?:ça me donne une idée(?: de| pour)?)\s+(.+)",
    r"(?:idée(?: de| pour)?)\s+(.+)",
]

TODO_PRO_PATTERNS = [
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+traiter\s+(.+)",
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+préparer\s+(.+)",
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+envoyer\s+(.+)",
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+caler\s+(.+)",
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+organiser\s+(.+)",
    r"(?:il faut que je|je dois|je devrais|faudra|il faut)\s+planifier\s+(.+)",
    r"(?:préparer|envoyer|caler|organiser|planifier)\s+(.+)",
]


def contains_negation(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in NEGATION_PATTERNS)


def extract_time_hint(text: str) -> str | None:
    for label, value in TIME_HINTS.items():
        if label in text:
            return value
    return None


def remove_time_suffixes(item: str) -> str:
    cleaned = item
    for suffix in TIME_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
            break
    return cleaned


def clean_extracted_item(text: str, list_name: str | None = None) -> str:
    item = text.strip().lower()
    item = item.strip(" .,!?:;")
    item = remove_time_suffixes(item)

    prefixes = [
        "du ",
        "de la ",
        "de l'",
        "des ",
        "d'",
        "le ",
        "la ",
        "les ",
        "au ",
        "aux ",
    ]

    if list_name != "shopping":
        prefixes.extend(["un ", "une "])

    for prefix in prefixes:
        if item.startswith(prefix):
            item = item[len(prefix):]
            break

    item = re.sub(r"\s+", " ", item).strip()
    return item


def build_result(
    transcript: str,
    intent: str,
    item: str | None,
    confidence: float,
    list_name: str,
    time_hint: str | None = None,
    needs_confirmation: bool = True,
    source: str = "rule",
) -> dict[str, Any]:
    return {
        "transcript": transcript,
        "intent": intent,
        "item": item,
        "confidence": confidence,
        "list": list_name,
        "needs_confirmation": needs_confirmation,
        "time_hint": time_hint,
        "source": source,
        "decision": "add",
    }


def match_patterns(
    text: str,
    transcript: str,
    patterns: list[str],
    intent: str,
    list_name: str,
    confidence: float,
) -> dict[str, Any] | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = [g for g in match.groups() if g]
            if not groups:
                continue

            raw_item = groups[-1]
            item = clean_extracted_item(raw_item, list_name=list_name)

            return build_result(
                transcript=transcript,
                intent=intent,
                item=item if item else None,
                confidence=confidence,
                list_name=list_name,
                time_hint=extract_time_hint(text),
            )
    return None


def extract_action(text: str) -> dict[str, Any]:
    transcript = text.strip()
    normalized = transcript.lower().strip()

    if not normalized:
        return build_result(
            transcript=transcript,
            intent="unknown",
            item=None,
            confidence=0.0,
            list_name="inbox",
            needs_confirmation=False,
        )

    if contains_negation(normalized):
        return build_result(
            transcript=transcript,
            intent="ignored_negative",
            item=None,
            confidence=0.9,
            list_name="inbox",
            needs_confirmation=False,
        )

    appointment = match_patterns(
        normalized,
        transcript,
        APPOINTMENT_PATTERNS,
        "appointment_add",
        "appointments",
        0.80,
    )
    if appointment:
        return appointment

    shopping = match_patterns(
        normalized,
        transcript,
        SHOPPING_PATTERNS,
        "shopping_add",
        "shopping",
        0.80,
    )
    if shopping:
        return shopping

    todo_pro = match_patterns(
        normalized,
        transcript,
        TODO_PRO_PATTERNS,
        "todo_pro_add",
        "todo_pro",
        0.78,
    )
    if todo_pro:
        pro_text = (todo_pro.get("item") or "").lower()
        if any(keyword in normalized for keyword in WORK_KEYWORDS) or any(
            keyword in pro_text for keyword in WORK_KEYWORDS
        ):
            return todo_pro

    todo = match_patterns(
        normalized,
        transcript,
        TODO_PATTERNS,
        "todo_add",
        "todo",
        0.75,
    )
    if todo:
        return todo

    idea = match_patterns(
        normalized,
        transcript,
        IDEA_PATTERNS,
        "idea_add",
        "ideas",
        0.65,
    )
    if idea:
        return idea

    return {
        "transcript": transcript,
        "intent": "unknown",
        "item": None,
        "confidence": 0.20,
        "list": "inbox",
        "needs_confirmation": False,
        "time_hint": None,
        "source": "rule",
        "decision": "ignore",
    }


def extract_action_with_fallback(text: str) -> dict[str, Any]:
    result = extract_action(text)

    if result["intent"] != "unknown":
        result["decision"] = "confirm" if result["confidence"] < 0.7 else "add"
        return result

    normalized = text.lower().strip()

    if len(normalized.split()) < 3:
        result["decision"] = "ignore"
        return result

    trivial_phrases = {
        "ok",
        "oui",
        "bonjour",
        "salut",
        "merci",
        "bonsoir",
        "hein",
        "hum",
        "euh",
        "bah",
    }

    if normalized.strip(" .!?") in trivial_phrases:
        result["decision"] = "ignore"
        return result

    action_keywords = [
        "acheter",
        "racheter",
        "commander",
        "appeler",
        "envoyer",
        "faire",
        "traiter",
        "préparer",
        "réserver",
        "prendre rendez-vous",
        "caler",
        "idée",
        "manque",
        "plus de",
        "besoin",
        "devis",
        "réunion",
        "formation",
        "demande",
    ]

    if not any(keyword in normalized for keyword in action_keywords):
        result["decision"] = "ignore"
        return result

    llm = interpret_with_llm(text)
    if not llm:
        result["decision"] = "ignore"
        return result

    intent = llm.get("intent", "none")
    item = llm.get("item")
    if isinstance(item, str):
        item = item.lower().strip()
    time_hint = llm.get("time_hint")

    if item in ("null", "", "none", "None"):
        item = None

    if time_hint in (
        "null",
        "",
        "none",
        "None",
        "now",
        "maintenant",
        "today",
        "aujourd'hui",
    ):
        time_hint = None

    if intent == "none" or not item:
        result["decision"] = "ignore"
        return result

    list_map = {
        "shopping_add": "shopping",
        "todo_add": "todo",
        "todo_pro_add": "todo_pro",
        "appointment_add": "appointments",
        "idea_add": "ideas",
    }

    return {
        "transcript": text,
        "intent": intent,
        "item": item,
        "confidence": 0.6,
        "list": list_map.get(intent, "inbox"),
        "needs_confirmation": True,
        "time_hint": time_hint,
        "source": "llm",
        "decision": "confirm",
    }