"""
Regression tests for bugs fixed in the refactoring session:
  1. rename_item no longer calls learn_synonym
  2. French decimal "0,75" is parsed correctly (qty=0.75, not raw text)
  3. Quantity is NOT duplicated in the stored text after rename with qty
  4. Quantity fusion: 20 poires + 3 poires = 23 poires (one entry)
"""
import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures (mirrors test_storage.py approach)
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    for name in ["shopping", "todo", "todo_pro", "appointments", "ideas"]:
        (tmp_path / f"{name}.json").write_text("[]")
    (tmp_path / "pending.json").write_text("[]")
    (tmp_path / "user_learning.json").write_text(
        '{"categories": {}, "synonyms": {}}'
    )
    return tmp_path


@pytest.fixture
def storage(data_dir):
    import app.storage as _storage
    import app.user_learning as _ul

    new_files = {
        "shopping":     data_dir / "shopping.json",
        "todo":         data_dir / "todo.json",
        "todo_pro":     data_dir / "todo_pro.json",
        "appointments": data_dir / "appointments.json",
        "ideas":        data_dir / "ideas.json",
    }
    new_pending  = data_dir / "pending.json"
    new_learning = data_dir / "user_learning.json"

    with (
        patch.object(_storage, "FILES",         new_files),
        patch.object(_storage, "PENDING_FILE",  new_pending),
        patch.object(_storage, "LEARNING_FILE", new_learning),
        patch.object(_ul,      "LEARNING_FILE", new_learning),
        patch("app.cleaning.categorize_with_llm", return_value=None),
        patch("app.cleaning.get_learned_category", return_value=None),
        patch("app.cleaning.get_learned_synonym",  return_value=None),
    ):
        yield _storage, data_dir


# ---------------------------------------------------------------------------
# Regression 1 — learn_synonym is NOT called from rename_item
# ---------------------------------------------------------------------------

class TestRenameDoesNotLearnSynonym:

    def test_rename_shopping_no_synonym_written(self, storage):
        """
        Renaming a shopping item (e.g. 'whisky' → 'whiskey') must not add
        any entry to the synonyms dict in user_learning.json.
        This was a regression where learn_synonym was called from rename_item.
        """
        mod, data_dir = storage

        mod.add_item("shopping", "whisky")
        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        learning_before = json.loads((data_dir / "user_learning.json").read_text())
        synonyms_before = dict(learning_before["synonyms"])

        mod.rename_item("shopping", item_id, "whiskey")

        learning_after = json.loads((data_dir / "user_learning.json").read_text())
        assert learning_after["synonyms"] == synonyms_before, (
            "rename_item must not write synonyms into user_learning.json"
        )

    def test_learn_synonym_function_not_invoked_on_rename(self, storage):
        """
        Verify via mock that learn_synonym is never called when renaming.
        """
        mod, data_dir = storage

        mod.add_item("shopping", "pomme")
        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        with patch.object(mod, "learn_synonym") as mock_learn:
            mod.rename_item("shopping", item_id, "pommes")
            mock_learn.assert_not_called()


# ---------------------------------------------------------------------------
# Regression 2 — French decimal "0,75" parsed as qty=0.75
# ---------------------------------------------------------------------------

class TestFrenchDecimalParsing:

    def test_075_cl_whiskey_quantity(self):
        """
        '0,75 cl whiskey' must yield qty=0.75, unit='cl', text='whiskey'.
        Previously the comma was not handled and the raw token ended up in text.
        """
        with (
            patch("app.cleaning.categorize_with_llm", return_value=None),
            patch("app.cleaning.get_learned_category", return_value=None),
            patch("app.cleaning.get_learned_synonym",  return_value=None),
        ):
            from app.cleaning import parse_shopping_item
            result = parse_shopping_item("0,75 cl whiskey")

        assert result["quantity"] == 0.75, (
            f"Expected qty=0.75, got {result['quantity']!r}. "
            "French comma decimal not parsed."
        )
        assert result["unit"] == "cl"
        assert result["text"] == "whiskey"

    def test_075_not_in_text(self):
        """After parsing, '0,75' must not appear inside the text field."""
        with (
            patch("app.cleaning.categorize_with_llm", return_value=None),
            patch("app.cleaning.get_learned_category", return_value=None),
            patch("app.cleaning.get_learned_synonym",  return_value=None),
        ):
            from app.cleaning import parse_shopping_item
            result = parse_shopping_item("0,75 cl whiskey")

        assert "0,75" not in result["text"]
        assert "0.75" not in result["text"]


# ---------------------------------------------------------------------------
# Regression 3 — Quantity NOT duplicated in stored text after rename
# ---------------------------------------------------------------------------

class TestQuantityNotDuplicatedInText:

    def test_rename_with_qty_text_is_clean(self, storage):
        """
        After rename_item("shopping", id, "10 poires"):
          - text stored must be "poires" (not "10 poires")
          - quantity stored must be 10
        """
        mod, data_dir = storage

        mod.add_item("shopping", "pommes")
        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        mod.rename_item("shopping", item_id, "10 poires")

        data = json.loads((data_dir / "shopping.json").read_text())
        entry = data[0]

        assert entry["text"] == "poires", (
            f"text should be 'poires', got {entry['text']!r}. "
            "Quantity was duplicated in the text field."
        )
        assert entry["quantity"] == 10

    def test_rename_without_qty_text_is_clean(self, storage):
        """rename to a bare noun: text stored must be that noun, qty None."""
        mod, data_dir = storage

        mod.add_item("shopping", "pommes", quantity=5)
        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        mod.rename_item("shopping", item_id, "poires")

        data = json.loads((data_dir / "shopping.json").read_text())
        entry = data[0]

        assert entry["text"] == "poires"


# ---------------------------------------------------------------------------
# Regression 4 — Quantity fusion: 20 poires + 3 poires = 23 poires
# ---------------------------------------------------------------------------

class TestQuantityFusion:

    def test_add_20_then_3_poires(self, storage):
        """
        add_item("shopping", "poires", quantity=20)
        add_item("shopping", "poires", quantity=3)
        → one item with quantity=23
        """
        mod, data_dir = storage

        mod.add_item("shopping", "poires", quantity=20)
        mod.add_item("shopping", "poires", quantity=3)

        data = json.loads((data_dir / "shopping.json").read_text())

        assert len(data) == 1, (
            f"Expected 1 merged entry, got {len(data)}. "
            "Quantities were not fused."
        )
        assert data[0]["quantity"] == 23, (
            f"Expected qty=23, got {data[0]['quantity']}."
        )

    def test_add_with_unit_fusion(self, storage):
        """3 kg farine + 2 kg farine = 5 kg farine."""
        mod, data_dir = storage

        mod.add_item("shopping", "farine", quantity=3, unit="kg")
        mod.add_item("shopping", "farine", quantity=2, unit="kg")

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 1
        assert data[0]["quantity"] == 5
        assert data[0]["unit"] == "kg"

    def test_no_fusion_different_units(self, storage):
        """2 kg pommes + 3 pommes (no unit) → 2 separate items."""
        mod, data_dir = storage

        mod.add_item("shopping", "pommes", quantity=2, unit="kg")
        mod.add_item("shopping", "pommes", quantity=3, unit=None)

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 2, (
            "Items with incompatible units must NOT be merged."
        )
