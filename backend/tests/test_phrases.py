from app.action_extractor import extract_action
import json


TEST_PHRASES = [
    "il faut acheter du lait",
    "on n a plus de café",
    "on n'a plus de sucre",
    "il faut appeler le plombier",
    "pense à appeler le dentiste demain",
    "il faut prendre rendez-vous chez le dentiste",
    "il faut réserver un restaurant",
    "il ne faut pas acheter de lait",
    "il faudrait envoyer le devis",
    "il faut faire la déclaration d'impôts",
    "on n'a plus de papier toilette",
    "il nous faut du beurre",
    "racheter du café",
    "commander des piles",
    "il faudrait envoyer le devis",
    "il faudrait appeler la banque demain",
    "il faudrait acheter du pain",
    "il faudrait prendre rendez-vous chez le médecin",
]


def main() -> None:
    print("=== TEST EXTRACTEUR ===\n")

    for phrase in TEST_PHRASES:
        result = extract_action(phrase)
        print(f"Phrase : {phrase}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 60)


if __name__ == "__main__":
    main()