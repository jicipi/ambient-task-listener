import re
from app.action_extractor import extract_action_with_fallback as extract_action

SPLIT_PATTERNS = [
    r"\bet puis\b",
    r"\bpuis\b",
    r"\bensuite\b",
    r",",
]


VERB_PREFIXES = [
    "il faut appeler ",
    "pense à appeler ",
    "faudra appeler ",
    "il faudrait appeler ",
    "faut appeler ",
]


def split_transcript(text: str):
    pattern = "|".join(SPLIT_PATTERNS)
    parts = re.split(pattern, text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts


def propagate_context(segments):
    if not segments:
        return segments

    rebuilt = []
    last_prefix = None

    for segment in segments:
        normalized = segment.strip().lower()

        found_prefix = None
        for prefix in VERB_PREFIXES:
            if normalized.startswith(prefix):
                found_prefix = prefix
                break

        if found_prefix:
            last_prefix = found_prefix
            rebuilt.append(segment)
            continue

        if last_prefix:
            rebuilt.append(last_prefix + normalized)
        else:
            rebuilt.append(segment)

    return rebuilt


def extract_multiple_actions(transcript: str):
    segments = split_transcript(transcript)
    segments = propagate_context(segments)

    results = []

    for segment in segments:
        result = extract_action(segment)

        if result["intent"] != "unknown" and result["item"]:
            results.append(result)

    return results