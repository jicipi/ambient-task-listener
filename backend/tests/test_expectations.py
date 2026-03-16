from app.action_extractor import extract_action


TEST_CASES = [
    {
        "text": "il faut acheter du lait",
        "intent": "shopping_add",
        "item": "lait",
        "time_hint": None,
    },
    {
        "text": "on n a plus de café",
        "intent": "shopping_add",
        "item": "café",
        "time_hint": None,
    },
    {
        "text": "pense à appeler le dentiste demain",
        "intent": "todo_add",
        "item": "dentiste",
        "time_hint": "tomorrow",
    },
    {
        "text": "il faut prendre rendez-vous chez le dentiste",
        "intent": "appointment_add",
        "item": "dentiste",
        "time_hint": None,
    },
    {
        "text": "il ne faut pas acheter de lait",
        "intent": "ignored_negative",
        "item": None,
        "time_hint": None,
    },
    {
        "text": "il faudrait envoyer le devis",
        "intent": "todo_add",
        "item": "devis",
        "time_hint": None,
    },
]


def main() -> None:
    failures = []

    for case in TEST_CASES:
        result = extract_action(case["text"])

        if result["intent"] != case["intent"]:
            failures.append(
                f'intent mismatch for "{case["text"]}": '
                f'expected {case["intent"]}, got {result["intent"]}'
            )

        if result["item"] != case["item"]:
            failures.append(
                f'item mismatch for "{case["text"]}": '
                f'expected {case["item"]}, got {result["item"]}'
            )

        if result["time_hint"] != case["time_hint"]:
            failures.append(
                f'time_hint mismatch for "{case["text"]}": '
                f'expected {case["time_hint"]}, got {result["time_hint"]}'
            )

    if failures:
        print("TESTS FAILED:\n")
        for failure in failures:
            print("-", failure)
        raise SystemExit(1)

    print("All expectation tests passed.")


if __name__ == "__main__":
    main()