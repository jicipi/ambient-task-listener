import json
from pathlib import Path

DATA_DIR = Path("data")


def load(name):
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def show(title, items):
    print("\n" + title)
    print("-" * len(title))
    for i in items:
        print("-", i["text"])


shopping = load("shopping")
todo = load("todo")
todo_pro = load("todo_pro")
appointments = load("appointments")
ideas = load("ideas")

show("COURSES", shopping)
show("TODO", todo)
show("TODO PRO", todo_pro)
show("RENDEZ-VOUS", appointments)
show("IDÉES", ideas)