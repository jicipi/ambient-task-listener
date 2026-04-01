import json
import requests

from app.logger import get_logger

logger = get_logger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

PROMPT = """
You extract actionable items from French spoken sentences.

Return ONLY valid JSON.
No markdown. No explanation.

Possible intents:
- shopping_add
- todo_add
- todo_pro_add
- appointment_add
- idea_add
- none

Interpretation rules:
- shopping_add: groceries, household products, things to buy, things that are missing at home
- todo_add: actions to do, people to call, things to send, tasks to complete
- todo_pro_add: professional tasks related to clients, meetings, training, workshops, projects, deliverables, quotes, requests
- appointment_add: appointments to schedule, bookings, reservations
- idea_add: ideas, jokes, wordplay, project ideas, creative notes, thoughts to keep

Examples:

Sentence: "il faut acheter du lait"
Output:
{"intent":"shopping_add","item":"lait","time_hint":null}

Sentence: "on n'a plus de café"
Output:
{"intent":"shopping_add","item":"café","time_hint":null}

Sentence: "pense à appeler le plombier demain"
Output:
{"intent":"todo_add","item":"plombier","time_hint":"tomorrow"}

Sentence: "il faut que je traite la demande de Pierre"
Output:
{"intent":"todo_pro_add","item":"la demande de Pierre","time_hint":null}

Sentence: "je dois caler une session de formation mardi"
Output:
{"intent":"todo_pro_add","item":"une session de formation","time_hint":"tuesday"}

Sentence: "il faut prendre rendez-vous chez le dentiste"
Output:
{"intent":"appointment_add","item":"dentiste","time_hint":null}

Sentence: "au fait on manque de café"
Output:
{"intent":"shopping_add","item":"café","time_hint":null}

Sentence: "j'ai une idée de blague"
Output:
{"intent":"idea_add","item":"blague","time_hint":null}

Sentence:
"""

def interpret_with_llm(text: str):
    payload = {
        "model": MODEL,
        "prompt": PROMPT + text,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 80,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=5)
        response.raise_for_status()

        data = response.json()
        raw = data.get("response", "").strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "intent": "none",
                "item": None,
                "time_hint": None,
                "_raw": raw,
            }

    except requests.exceptions.ConnectionError:
        logger.warning("Ollama indisponible — fallback LLM ignoré")
        return None
    except requests.exceptions.Timeout:
        logger.warning("Ollama timeout (5s dépassé) — fallback LLM ignoré")
        return None
    except Exception as e:
        logger.warning("Ollama erreur inattendue : %s", e)
        return None


MULTI_PROMPT = """
You extract multiple actionable items from a single French spoken sentence.

Return ONLY a valid JSON array. No markdown. No explanation.

Each element in the array must have:
- "intent": one of shopping_add, todo_add, todo_pro_add, appointment_add, idea_add
- "item": the extracted item (string)
- "time_hint": a time hint if present, otherwise null

Interpretation rules:
- shopping_add: groceries, household products, things to buy
- todo_add: actions to do, people to call, things to send, tasks to complete
- todo_pro_add: professional tasks (clients, meetings, training, projects, quotes)
- appointment_add: appointments to schedule, bookings
- idea_add: ideas, creative notes, thoughts to keep

Examples:

Sentence: "achète du lait et appelle le médecin demain"
Output:
[{"intent":"shopping_add","item":"lait","time_hint":null},{"intent":"todo_add","item":"médecin","time_hint":"tomorrow"}]

Sentence: "ajoute des pommes et des oranges"
Output:
[{"intent":"shopping_add","item":"pommes","time_hint":null},{"intent":"shopping_add","item":"oranges","time_hint":null}]

Sentence: "pense à appeler le dentiste et à commander les médicaments"
Output:
[{"intent":"todo_add","item":"dentiste","time_hint":null},{"intent":"shopping_add","item":"médicaments","time_hint":null}]

Sentence:
"""


def interpret_multiple_with_llm(text: str) -> list[dict] | None:
    """Demande au LLM d'extraire plusieurs actions depuis une phrase."""
    payload = {
        "model": MODEL,
        "prompt": MULTI_PROMPT + text,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 300,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=5)
        response.raise_for_status()

        data = response.json()
        raw = data.get("response", "").strip()

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            # LLM may have returned a single object — wrap it
            if isinstance(parsed, dict):
                return [parsed]
            return None
        except json.JSONDecodeError:
            logger.warning("interpret_multiple_with_llm: JSON invalide : %s", raw)
            return None

    except requests.exceptions.ConnectionError:
        logger.warning("Ollama indisponible — fallback LLM multi ignoré")
        return None
    except requests.exceptions.Timeout:
        logger.warning("Ollama timeout (5s) — fallback LLM multi ignoré")
        return None
    except Exception as e:
        logger.warning("Ollama erreur inattendue (multi) : %s", e)
        return None


def categorize_with_llm(text: str) -> str | None:
    try:
        result = interpret_with_llm(
            f"Catégorise cet élément: {text}. "
            "Réponds uniquement par une catégorie parmi: "
            "fruits, légumes, viande, poisson, produits laitiers, épicerie, ménager, autres."
        )

        if not result:
            return None

        category = result.get("category") if isinstance(result, dict) else str(result)

        if not category:
            return None

        category = category.strip().lower()

        allowed = {
            "fruits",
            "légumes",
            "viande",
            "poisson",
            "produits laitiers",
            "épicerie",
            "ménager",
            "autres",
        }

        if category in allowed:
            return category

        return None

    except Exception as e:
        logger.error("Erreur LLM catégorisation : %s", e)
        return None