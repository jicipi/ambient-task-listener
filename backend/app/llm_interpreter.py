import json
import requests

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
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        raw = data.get("response", "").strip()

        #print("RAW OLLAMA RESPONSE:", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "intent": "none",
                "item": None,
                "time_hint": None,
                "_raw": raw,
            }

    except requests.exceptions.Timeout:
        print("LLM timeout")
        return None
    except Exception as e:
        print("LLM error:", e)
        return None