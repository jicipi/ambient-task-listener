from app.action_extractor import extract_action_with_fallback


def extract_multiple_actions(transcript: str) -> list[dict]:
    """Extrait une ou plusieurs actions depuis un transcript.

    Délègue au nouveau moteur extract_action_with_fallback qui gère
    nativement le multi-action. Retourne toujours une liste de dicts.
    """
    result = extract_action_with_fallback(transcript)

    if result.get("multi"):
        return result["actions"]

    if result.get("intent", "unknown") != "unknown" and result.get("item"):
        return [result]

    return [result]
