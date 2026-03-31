"""
Tests for storage.py operations: add_item, rename_item, update_shopping_item,
delete_item, update_item_done, _canonicalize_for_dedupe.

Each test uses a tmp_path fixture so it never touches the real data/ directory.
LLM and user_learning side-effects are patched to stay deterministic.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    """Create minimal JSON files expected by storage.py in a temp directory."""
    for name in ["shopping", "todo", "todo_pro", "appointments", "ideas"]:
        (tmp_path / f"{name}.json").write_text("[]")
    (tmp_path / "pending.json").write_text("[]")
    (tmp_path / "user_learning.json").write_text(
        '{"categories": {}, "synonyms": {}}'
    )
    return tmp_path


@pytest.fixture
def storage(data_dir):
    """
    Return the storage module with FILES, PENDING_FILE and LEARNING_FILE
    redirected to data_dir.  Also patches user_learning.py's LEARNING_FILE
    and the LLM categorizer.
    """
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
# _canonicalize_for_dedupe
# ---------------------------------------------------------------------------

class TestCanonicalizeForDedupe:

    def test_todo_strips_leading_action_word(self, storage):
        mod, _ = storage
        assert mod._canonicalize_for_dedupe("todo", "appeler le plombier") == "plombier"

    def test_todo_strips_article(self, storage):
        mod, _ = storage
        assert mod._canonicalize_for_dedupe("todo", "faire la vaisselle") == "vaisselle"

    def test_shopping_no_stripping(self, storage):
        mod, _ = storage
        # For shopping lists, action words are NOT stripped
        result = mod._canonicalize_for_dedupe("shopping", "pommes")
        assert result == "pommes"

    def test_common_correction_applied(self, storage):
        mod, _ = storage
        result = mod._canonicalize_for_dedupe("todo", "fondier")
        assert result == "plombier"


# ---------------------------------------------------------------------------
# add_item — todo
# ---------------------------------------------------------------------------

class TestAddItemTodo:

    def test_simple_add(self, storage):
        mod, data_dir = storage
        result = mod.add_item("todo", "appeler le plombier")
        assert result is True

        data = json.loads((data_dir / "todo.json").read_text())
        assert len(data) == 1
        assert data[0]["text"] == "appeler le plombier"
        assert data[0]["done"] is False

    def test_invalid_empty_text(self, storage):
        mod, data_dir = storage
        result = mod.add_item("todo", "")
        assert result is False
        data = json.loads((data_dir / "todo.json").read_text())
        assert len(data) == 0

    def test_invalid_too_short(self, storage):
        mod, data_dir = storage
        result = mod.add_item("todo", "ok")   # 2 chars, in STOP_ITEMS too
        assert result is False

    def test_stop_word_rejected(self, storage):
        mod, data_dir = storage
        result = mod.add_item("todo", "merci")
        assert result is False

    def test_unknown_list_rejected(self, storage):
        mod, _ = storage
        result = mod.add_item("nonexistent", "bananes")
        assert result is False


# ---------------------------------------------------------------------------
# add_item — shopping merging
# ---------------------------------------------------------------------------

class TestAddItemShoppingMerge:

    def test_merge_same_item_same_unit(self, storage):
        """3 bananes + 2 bananes = 5 bananes (single entry)."""
        mod, data_dir = storage
        mod.add_item("shopping", "bananes", quantity=3)
        mod.add_item("shopping", "bananes", quantity=2)

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 1
        assert data[0]["quantity"] == 5

    def test_no_merge_incompatible_units(self, storage):
        """2 kg pommes + 3 pommes → 2 separate items (different units)."""
        mod, data_dir = storage
        mod.add_item("shopping", "pommes", quantity=2, unit="kg")
        mod.add_item("shopping", "pommes", quantity=3, unit=None)

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 2

    def test_merge_both_no_quantity(self, storage):
        """Two entries without quantity → deduplicate to one."""
        mod, data_dir = storage
        mod.add_item("shopping", "lait")
        mod.add_item("shopping", "lait")

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 1

    def test_enrich_no_quantity_then_with_same_unit(self, storage):
        """
        First add without quantity and without unit, then again without unit
        but with a quantity → existing entry gets enriched (units_compatible:
        both None), still one item.
        """
        mod, data_dir = storage
        mod.add_item("shopping", "lait")
        mod.add_item("shopping", "lait", quantity=2)  # unit=None on both sides

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 1
        assert data[0]["quantity"] == 2
        assert data[0]["unit"] is None

    def test_no_enrich_when_unit_changes(self, storage):
        """
        Existing entry has no unit; new entry adds a unit → units_compatible
        is False (None != 'l'), so the entries are NOT merged.
        """
        mod, data_dir = storage
        mod.add_item("shopping", "lait")
        mod.add_item("shopping", "lait", quantity=2, unit="l")

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 2

    def test_different_items_not_merged(self, storage):
        mod, data_dir = storage
        mod.add_item("shopping", "lait")
        mod.add_item("shopping", "beurre")

        data = json.loads((data_dir / "shopping.json").read_text())
        assert len(data) == 2


# ---------------------------------------------------------------------------
# rename_item
# ---------------------------------------------------------------------------

class TestRenameItem:

    def test_rename_shopping_parses_quantity_and_unit(self, storage):
        """rename to '1 l whiskey' → text='whiskey', qty=1, unit='l'"""
        mod, data_dir = storage
        mod.add_item("shopping", "whisky", quantity=None)

        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        result = mod.rename_item("shopping", item_id, "1 l whiskey")
        assert result is True

        data = json.loads((data_dir / "shopping.json").read_text())
        assert data[0]["text"] == "whiskey"
        assert data[0]["quantity"] == 1
        assert data[0]["unit"] == "l"

    def test_rename_does_not_store_synonym(self, storage):
        """
        Renaming a shopping item must NOT write anything into
        user_learning.json synonyms section.
        """
        mod, data_dir = storage
        mod.add_item("shopping", "pomme", quantity=None)

        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        learning_before = json.loads((data_dir / "user_learning.json").read_text())
        mod.rename_item("shopping", item_id, "pommes")
        learning_after = json.loads((data_dir / "user_learning.json").read_text())

        assert learning_before["synonyms"] == learning_after["synonyms"]

    def test_rename_todo_item(self, storage):
        mod, data_dir = storage
        mod.add_item("todo", "appeler le plombier")

        data = json.loads((data_dir / "todo.json").read_text())
        item_id = data[0]["id"]

        result = mod.rename_item("todo", item_id, "appeler le médecin")
        assert result is True

        data = json.loads((data_dir / "todo.json").read_text())
        assert data[0]["text"] == "appeler le médecin"

    def test_rename_nonexistent_id_returns_false(self, storage):
        mod, _ = storage
        result = mod.rename_item("todo", "nonexistent-id", "quelque chose")
        assert result is False


# ---------------------------------------------------------------------------
# delete_item
# ---------------------------------------------------------------------------

class TestDeleteItem:

    def test_delete_existing(self, storage):
        mod, data_dir = storage
        mod.add_item("todo", "appeler le plombier")

        data = json.loads((data_dir / "todo.json").read_text())
        item_id = data[0]["id"]

        result = mod.delete_item("todo", item_id)
        assert result is True

        data = json.loads((data_dir / "todo.json").read_text())
        assert len(data) == 0

    def test_delete_nonexistent_returns_false(self, storage):
        mod, _ = storage
        result = mod.delete_item("todo", "no-such-id")
        assert result is False


# ---------------------------------------------------------------------------
# update_item_done
# ---------------------------------------------------------------------------

class TestUpdateItemDone:

    def test_toggle_done_true(self, storage):
        mod, data_dir = storage
        mod.add_item("todo", "appeler le plombier")

        data = json.loads((data_dir / "todo.json").read_text())
        item_id = data[0]["id"]

        result = mod.update_item_done("todo", item_id, True)
        assert result is True

        data = json.loads((data_dir / "todo.json").read_text())
        assert data[0]["done"] is True

    def test_toggle_done_false(self, storage):
        mod, data_dir = storage
        mod.add_item("todo", "appeler le plombier")

        data = json.loads((data_dir / "todo.json").read_text())
        item_id = data[0]["id"]

        mod.update_item_done("todo", item_id, True)
        mod.update_item_done("todo", item_id, False)

        data = json.loads((data_dir / "todo.json").read_text())
        assert data[0]["done"] is False

    def test_update_done_nonexistent(self, storage):
        mod, _ = storage
        result = mod.update_item_done("todo", "no-id", True)
        assert result is False


# ---------------------------------------------------------------------------
# update_shopping_item
# ---------------------------------------------------------------------------

class TestUpdateShoppingItem:

    def test_update_text_quantity_unit(self, storage):
        mod, data_dir = storage
        mod.add_item("shopping", "poires", quantity=5)

        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        result = mod.update_shopping_item(
            item_id=item_id,
            text="poires",
            quantity=10,
            unit=None,
            category="fruits",
        )
        assert result is True

        data = json.loads((data_dir / "shopping.json").read_text())
        assert data[0]["quantity"] == 10
        assert data[0]["text"] == "poires"
        assert data[0]["category"] == "fruits"

    def test_update_invalid_text_returns_false(self, storage):
        mod, data_dir = storage
        mod.add_item("shopping", "poires", quantity=5)

        data = json.loads((data_dir / "shopping.json").read_text())
        item_id = data[0]["id"]

        result = mod.update_shopping_item(item_id=item_id, text="")
        assert result is False
