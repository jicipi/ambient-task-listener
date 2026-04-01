from __future__ import annotations

import re
from typing import Any

from app.llm_interpreter import interpret_with_llm, interpret_multiple_with_llm
from app.date_parser import parse_french_date
from app.asr_corrections import correct_transcript, is_likely_shopping_mishearing


def get_confidence_thresholds() -> tuple[float, float]:
    """Retourne (add_threshold, ignore_threshold) depuis les settings persistés."""
    from app.storage import get_setting
    add_threshold = float(get_setting("confidence_add_threshold", "0.7"))
    ignore_threshold = float(get_setting("confidence_ignore_threshold", "0.35"))
    return add_threshold, ignore_threshold


PRIORITY_HIGH_KEYWORDS = [
    "urgent",
    "rapidement",
    "vite",
    "immédiatement",
    "aujourd'hui",
    "ce matin",
    "maintenant",
    "dès que possible",
    "asap",
]

PRIORITY_LOW_KEYWORDS = [
    "un jour",
    "à terme",
    "quand j'aurai le temps",
    "éventuellement",
    "peut-être",
]

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
    r"je\s+dois\s+ach[eè]t\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"je\s+devrais\s+ach[eè]t\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"je\s+vais\s+devoir\s+ach[eè]t\w*\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    rf"(?:{LEADERS})?\s*(?:ach[eè]t\w*|rach[eè]t\w*|command\w*|ajout\w*|rajout\w*|prendre)\s+(.+?)(?:\s+à\s+la\s+liste)?$",
    r"on\s+a\s+(?:bientôt|presque|presque\s+plus)\s+plus\s+de\s+(.+?)(?:\s*,.*)?$",
    r"(?:on|il|elle|je|tu|[\w]+)\s+n['\u2019]?a\s+plus\s+de\s+(.+)",
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
    r"n[‘’]oublie\s+pas\s+de\s+(.+)",
    r"(?:il faut que j[‘’]|je dois|je devrais|faut que j[‘’]|il faudrait que j[‘’])\s*emm[eè]ne?\s+(.+)$",
    r"(?:il faut|il faudrait|faut|pense à|n’oublie pas de)\s+emm[eè]ner?\s+(.+)$",
    # Impératifs nus (dans un segment multi-actions isolé du contexte)
    r"^appell\w*\s+(?:le|la|les|l[‘’]|un|une|du|de|au|à)?\s*(.+)",
    r"^envoie\s+(?:le|la|les|l[‘’]|un|une|du|de|à)?\s*(.+)",
    r"^rappelle\w*\s+(?:le|la|les|l[‘’]|un|une|du|de|moi|toi)?\s*(.+)",
]

_DAYS = r"(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|demain|ce\s+soir|ce\s+week-end)"
_EVENT_TYPES = (
    r"(?:entraînement|cours|match|rdv|rendez.vous|séance|réunion"
    r"|formation|atelier|tournoi|compétition|concert|spectacle)"
)

APPOINTMENT_PATTERNS = [
    rf"(?:{LEADERS})?\s*prendre\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
    r"(?:prends|prenez)\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
    rf"(?:{LEADERS})\s*réserver\s+(.+)",
    rf"(?:{PERSONAL_LEADERS})(?:prenne|prendre)\s+rendez[- ]vous\s+(?:chez|avec)?\s*(.+)",
    # "j'ai [event de X] [jour] [heure optionnelle]"
    rf"j['\u2019]ai\s+(?:un\s+|une\s+|mon\s+|ma\s+)?({_EVENT_TYPES}(?:\s+(?:de|d['\u2019])?\s*\w+(?:\s+\w+)?)?)\s+{_DAYS}",
    # "j'ai [event] [jour]" — formulation naturelle générique
    rf"j['\u2019]ai\s+(?:un\s+|une\s+|mon\s+|ma\s+)?({_EVENT_TYPES})\s+{_DAYS}",
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


def compute_priority(text: str, intent: str, time_hint: str | None = None) -> int:
    """Retourne la priorité (1=haute, 2=normale, 3=basse) selon le texte et l'intent."""
    normalized = text.lower()

    # Priorité basse : idées ou mots-clés bas
    if intent == "idea_add":
        return 3
    if any(kw in normalized for kw in PRIORITY_LOW_KEYWORDS):
        return 3

    # Priorité haute : mots-clés urgence
    if any(kw in normalized for kw in PRIORITY_HIGH_KEYWORDS):
        return 1

    # Priorité haute : RDV aujourd'hui ou demain
    if intent == "appointment_add" and time_hint in ("today", "tomorrow"):
        return 1

    return 2


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
    priority: int | None = None,
) -> dict[str, Any]:
    # Parse scheduled_date from time_hint for appointments
    scheduled_date: str | None = None
    if intent == "appointment_add" and time_hint:
        scheduled_date = parse_french_date(time_hint)

    if priority is None:
        priority = compute_priority(transcript, intent, time_hint)

    return {
        "transcript": transcript,
        "intent": intent,
        "item": item,
        "confidence": confidence,
        "list": list_name,
        "needs_confirmation": needs_confirmation,
        "time_hint": time_hint,
        "scheduled_date": scheduled_date,
        "source": source,
        "priority": priority,
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
    transcript = correct_transcript(transcript)
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

    ADVERB_ONLY_ITEMS = {
        "beaucoup", "assez", "trop", "peu", "plein", "encore", "plus", "moins", "autant",
    }

    shopping = match_patterns(
        normalized,
        transcript,
        SHOPPING_PATTERNS,
        "shopping_add",
        "shopping",
        0.80,
    )
    if shopping:
        item_text = shopping.get("item") or ""
        if item_text.strip().lower() in ADVERB_ONLY_ITEMS:
            return build_result(
                transcript=transcript,
                intent="unknown",
                item=None,
                confidence=0.0,
                list_name="inbox",
                needs_confirmation=False,
            )
        if is_likely_shopping_mishearing(item_text):
            shopping["confidence"] = min(shopping.get("confidence", 0.8), 0.45)
            shopping["needs_confirmation"] = True
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
        "priority": compute_priority(transcript, "unknown"),
        "decision": "ignore",
    }


# ---------------------------------------------------------------------------
# Connecteurs utilisés pour le découpage multi-actions
# ---------------------------------------------------------------------------

MULTI_ACTION_CONNECTORS = [" et ", " puis ", " aussi ", " en plus ", " de plus "]

# Verbes d'action reconnus dans un segment pour valider qu'il est autonome
ACTION_VERBS = [
    "achète", "acheter", "achet",
    "rachète", "racheter",
    "commande", "commander",
    "ajoute", "ajouter", "rajoute", "rajouter",
    "appelle", "appeler",
    "envoie", "envoyer",
    "fais", "faire",
    "prends", "prendre",
    "réserve", "réserver",
    "pense", "penser",
    "n'oublie", "oublie",
    "traite", "prépare", "cale", "organise",
    "il faut", "je dois", "faudra",
]


def _segment_is_valid_action(segment: str) -> bool:
    """
    Retourne True si le segment semble contenir une action indépendante :
    - au moins 3 mots
    - contient un verbe d'action reconnu
    """
    words = segment.strip().split()
    if len(words) < 2:
        return False
    seg_lower = segment.lower()
    return any(verb in seg_lower for verb in ACTION_VERBS)


def _build_result_from_llm_item(text: str, llm_item: dict) -> dict[str, Any] | None:
    """Convertit un élément LLM multi en résultat standard."""
    intent = llm_item.get("intent", "none")
    item = llm_item.get("item")
    time_hint = llm_item.get("time_hint")

    if isinstance(item, str):
        item = item.lower().strip()
    if item in ("null", "", "none", "None", None):
        return None
    if isinstance(time_hint, str) and time_hint in (
        "null", "", "none", "None", "now", "maintenant", "today", "aujourd'hui"
    ):
        time_hint = None
    if intent == "none" or not item:
        return None

    list_map = {
        "shopping_add": "shopping",
        "todo_add": "todo",
        "todo_pro_add": "todo_pro",
        "appointment_add": "appointments",
        "idea_add": "ideas",
    }

    scheduled_date: str | None = None
    if intent == "appointment_add" and time_hint:
        scheduled_date = parse_french_date(time_hint)

    priority = compute_priority(text, intent, time_hint)

    return {
        "transcript": text,
        "intent": intent,
        "item": item,
        "confidence": 0.6,
        "list": list_map.get(intent, "inbox"),
        "needs_confirmation": True,
        "time_hint": time_hint,
        "scheduled_date": scheduled_date,
        "source": "llm",
        "priority": priority,
        "decision": "confirm",
    }


def _try_inherit_action(
    seg: str,
    template: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Pour un segment sans verbe (ex: "des oranges"), hérite de l'intent/list du template
    et extrait l'item via clean_extracted_item.
    Retourne None si le segment est vide après nettoyage.
    """
    item = clean_extracted_item(seg, list_name=template.get("list"))
    if not item:
        return None
    result = dict(template)
    result["transcript"] = seg
    result["item"] = item
    result["time_hint"] = extract_time_hint(seg.lower())
    result["scheduled_date"] = None
    return result


def extract_multiple_actions(text: str) -> list[dict[str, Any]]:
    """
    Tente d'extraire plusieurs actions d'une phrase contenant des connecteurs.

    Étape 1 : découpe sur les connecteurs — deux stratégies :
        a) les deux segments sont autonomes (ont un verbe d'action)
        b) seul le segment gauche a un verbe : le segment droit hérite de l'action gauche
    Étape 2 : extrait chaque segment via les règles (extract_action).
    Étape 3 : fallback LLM multi si < 2 résultats valides.
    """
    normalized = text.lower().strip()

    # --- Étape 1 : découper sur les connecteurs ---
    left_seg: str | None = None
    right_seg: str | None = None
    inherit_right = False  # True si le segment droit hérite de l'action gauche
    remaining = text.strip()

    for connector in MULTI_ACTION_CONNECTORS:
        if connector in remaining.lower():
            idx = remaining.lower().find(connector)
            left = remaining[:idx].strip()
            right = remaining[idx + len(connector):].strip()

            left_valid = _segment_is_valid_action(left)
            right_valid = _segment_is_valid_action(right)

            if left_valid and right_valid:
                # Les deux segments sont autonomes
                left_seg, right_seg = left, right
                inherit_right = False
                break
            elif left_valid and len(right.split()) >= 1:
                # Le segment droit est une phrase nominale : hériter de l'action gauche
                left_seg, right_seg = left, right
                inherit_right = True
                break

    # --- Étape 2 : extraire chaque segment via les règles ---
    results: list[dict[str, Any]] = []
    if left_seg is not None and right_seg is not None:
        add_threshold, ignore_threshold = get_confidence_thresholds()

        def _extract_seg(seg: str) -> dict[str, Any] | None:
            r = extract_action(seg)
            if r["intent"] != "unknown" and r["confidence"] >= 0.5:
                if r["confidence"] >= add_threshold:
                    r["decision"] = "add"
                elif r["confidence"] <= ignore_threshold:
                    r["decision"] = "ignore"
                else:
                    r["decision"] = "confirm"
                return r
            # Fallback LLM sur ce segment
            llm = interpret_with_llm(seg)
            if llm:
                return _build_result_from_llm_item(seg, llm)
            return None

        left_result = _extract_seg(left_seg)
        if left_result:
            results.append(left_result)

        if inherit_right and left_result:
            # Le segment droit hérite de l'intent/list du gauche
            right_result = _try_inherit_action(right_seg, left_result)
            if right_result:
                results.append(right_result)
        elif right_seg is not None:
            right_result = _extract_seg(right_seg)
            if right_result:
                results.append(right_result)

    # --- Étape 3 : fallback LLM multi si < 2 résultats valides ---
    if len(results) < 2 and any(c in normalized for c in [" et ", " puis ", " aussi "]):
        llm_list = interpret_multiple_with_llm(text)
        if llm_list and len(llm_list) >= 2:
            llm_results = []
            for llm_item in llm_list:
                built = _build_result_from_llm_item(text, llm_item)
                if built:
                    llm_results.append(built)
            if len(llm_results) >= 2:
                return llm_results

    return results


def extract_action_with_fallback(text: str, allow_multi: bool = True) -> dict[str, Any]:
    normalized_check = text.lower().strip()

    # --- Multi-action : si la phrase contient des connecteurs, tenter le découpage ---
    if allow_multi and any(c in normalized_check for c in MULTI_ACTION_CONNECTORS):
        multi_results = extract_multiple_actions(text)
        if len(multi_results) >= 2:
            return {"multi": True, "actions": multi_results}

    rules_result = extract_action(text)
    add_threshold, ignore_threshold = get_confidence_thresholds()
    rules_confidence = rules_result["confidence"]
    rules_intent = rules_result["intent"]

    list_map = {
        "shopping_add": "shopping",
        "todo_add": "todo",
        "todo_pro_add": "todo_pro",
        "appointment_add": "appointments",
        "idea_add": "ideas",
    }

    # --- Cas 1 : confiance règles >= seuil → décision directe sans LLM ---
    if rules_intent != "unknown" and rules_confidence >= add_threshold:
        rules_result["decision"] = "add"
        if "priority" not in rules_result:
            rules_result["priority"] = compute_priority(
                text, rules_intent, rules_result.get("time_hint")
            )
        return rules_result

    # --- Cas 2 : zone grise (0.2 < rules_confidence < add_threshold) ---
    if rules_intent != "unknown" and rules_confidence > 0.2:
        llm = interpret_with_llm(text)
        if llm:
            llm_intent = llm.get("intent", "none")
            llm_item = llm.get("item")
            if isinstance(llm_item, str):
                llm_item = llm_item.lower().strip()
            llm_time_hint = llm.get("time_hint")

            if llm_item in ("null", "", "none", "None"):
                llm_item = None
            if llm_time_hint in (
                "null", "", "none", "None", "now", "maintenant", "today", "aujourd'hui"
            ):
                llm_time_hint = None

            if llm_intent == "none" or not llm_item:
                # LLM retourne none → pénalité forte
                combined_confidence = rules_confidence * 0.6
                source = "combined"
            elif llm_intent == rules_intent:
                # LLM concorde → boost
                combined_confidence = (rules_confidence + 0.85) / 2
                source = "combined"
            else:
                # LLM diverge → pénalité doute
                combined_confidence = rules_confidence * 0.8
                source = "combined"

            rules_result["confidence"] = combined_confidence
            rules_result["source"] = source
            if combined_confidence >= add_threshold:
                rules_result["decision"] = "add"
            elif combined_confidence <= ignore_threshold:
                rules_result["decision"] = "ignore"
            else:
                rules_result["decision"] = "confirm"
            if "priority" not in rules_result:
                rules_result["priority"] = compute_priority(
                    text, rules_intent, rules_result.get("time_hint")
                )
            return rules_result

        # Pas de LLM disponible : décision basée sur les règles seules
        if rules_confidence >= add_threshold:
            rules_result["decision"] = "add"
        elif rules_confidence <= ignore_threshold:
            rules_result["decision"] = "ignore"
        else:
            rules_result["decision"] = "confirm"
        if "priority" not in rules_result:
            rules_result["priority"] = compute_priority(
                text, rules_intent, rules_result.get("time_hint")
            )
        return rules_result

    # --- Cas 3 : rules_confidence <= 0.2 ou intent unknown → fallback LLM direct ---
    normalized = text.lower().strip()

    if len(normalized.split()) < 3:
        rules_result["decision"] = "ignore"
        return rules_result

    trivial_phrases = {
        "ok", "oui", "bonjour", "salut", "merci", "bonsoir",
        "hein", "hum", "euh", "bah",
    }

    if normalized.strip(" .!?") in trivial_phrases:
        rules_result["decision"] = "ignore"
        return rules_result

    action_keywords = [
        "acheter", "racheter", "commander", "appeler", "appelle", "envoyer",
        "faire", "traiter", "préparer", "réserver", "prendre rendez-vous",
        "caler", "idée", "manque", "plus de", "besoin", "devis",
        "réunion", "formation", "demande",
    ]

    if not any(keyword in normalized for keyword in action_keywords):
        rules_result["decision"] = "ignore"
        return rules_result

    llm = interpret_with_llm(text)
    if not llm:
        rules_result["decision"] = "ignore"
        return rules_result

    intent = llm.get("intent", "none")
    item = llm.get("item")
    if isinstance(item, str):
        item = item.lower().strip()
    time_hint = llm.get("time_hint")

    if item in ("null", "", "none", "None"):
        item = None

    if time_hint in (
        "null", "", "none", "None", "now", "maintenant", "today", "aujourd'hui"
    ):
        time_hint = None

    if intent == "none" or not item:
        rules_result["decision"] = "ignore"
        return rules_result

    # Parse scheduled_date from time_hint for appointments (LLM path)
    scheduled_date: str | None = None
    if intent == "appointment_add" and time_hint:
        scheduled_date = parse_french_date(time_hint)

    priority = compute_priority(text, intent, time_hint)

    return {
        "transcript": text,
        "intent": intent,
        "item": item,
        "confidence": 0.65,
        "list": list_map.get(intent, "inbox"),
        "needs_confirmation": True,
        "time_hint": time_hint,
        "scheduled_date": scheduled_date,
        "source": "llm",
        "priority": priority,
        "decision": "confirm",
    }