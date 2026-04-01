"""
Tests for storage.py operations: add_item, rename_item, update_shopping_item,
delete_item, update_item_done, _canonicalize_for_dedupe.

Each test uses an isolated SQLite in-memory (or temp-file) database so it
never touches the real data/ directory.
LLM and user_learning side-effects are patched to stay deterministic.
"""
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def storage(tmp_path):
    """
    Return the storage module backed by an isolated SQLite database.
    The DB is created in a temp file so each test gets a clean slate.
    LLM side-effects are patched to be deterministic.
    """
    import app.database as _db
    import app.storage as _storage

    db_file = str(tmp_path / "test_ambient.db")

    # Point the database module at the temp DB, then re-initialise tables
    _db.set_db_path(db_file)
    _db.init_db()

    new_files = {
        "shopping":     tmp_path / "shopping.json",
        "todo":         tmp_path / "todo.json",
        "todo_pro":     tmp_path / "todo_pro.json",
        "appointments": tmp_path / "appointments.json",
        "ideas":        tmp_path / "ideas.json",
    }

    with (
        patch.object(_storage, "FILES", new_files),
        patch("app.cleaning.categorize_with_llm", return_value=None),
        patch("app.cleaning.get_learned_category", return_value=None),
        patch("app.cleaning.get_learned_synonym",  return_value=None),
    ):
        yield _storage

    # Reset to real DB path after each test
    import app.database as _db2
    from pathlib import Path
    _db2.set_db_path(str(Path(__file__).resolve().parent.parent / "data" / "ambient.db"))
    _db2.init_db()


# ---------------------------------------------------------------------------
# _canonicalize_for_dedupe
# ---------------------------------------------------------------------------

class TestCanonicalizeForDedupe:

    def test_todo_strips_leading_action_word(self, storage):
        assert storage._canonicalize_for_dedupe("todo", "appeler le plombier") == "plombier"

    def test_todo_strips_article(self, storage):
        assert storage._canonicalize_for_dedupe("todo", "faire la vaisselle") == "vaisselle"

    def test_shopping_no_stripping(self, storage):
        result = storage._canonicalize_for_dedupe("shopping", "pommes")
        assert result == "pommes"

    def test_common_correction_applied(self, storage):
        result = storage._canonicalize_for_dedupe("todo", "fondier")
        assert result == "plombier"


# ---------------------------------------------------------------------------
# add_item — todo
# ---------------------------------------------------------------------------

class TestAddItemTodo:

    def test_simple_add(self, storage):
        result = storage.add_item("todo", "appeler le plombier")
        assert result is True

        data = storage.get_list("todo")
        assert len(data) == 1
        assert data[0]["text"] == "appeler le plombier"
        assert data[0]["done"] is False

    def test_invalid_empty_text(self, storage):
        result = storage.add_item("todo", "")
        assert result is False
        assert len(storage.get_list("todo")) == 0

    def test_invalid_too_short(self, storage):
        result = storage.add_item("todo", "ok")
        assert result is False

    def test_stop_word_rejected(self, storage):
        result = storage.add_item("todo", "merci")
        assert result is False

    def test_unknown_list_rejected(self, storage):
        result = storage.add_item("nonexistent", "bananes")
        assert result is False


# ---------------------------------------------------------------------------
# add_item — shopping merging
# ---------------------------------------------------------------------------

class TestAddItemShoppingMerge:

    def test_merge_same_item_same_unit(self, storage):
        """3 bananes + 2 bananes = 5 bananes (single entry)."""
        storage.add_item("shopping", "bananes", quantity=3)
        storage.add_item("shopping", "bananes", quantity=2)

        data = storage.get_list("shopping")
        assert len(data) == 1
        assert data[0]["quantity"] == 5

    def test_no_merge_incompatible_units(self, storage):
        """2 kg pommes + 3 pommes → 2 separate items (different units)."""
        storage.add_item("shopping", "pommes", quantity=2, unit="kg")
        storage.add_item("shopping", "pommes", quantity=3, unit=None)

        data = storage.get_list("shopping")
        assert len(data) == 2

    def test_merge_both_no_quantity(self, storage):
        """Two entries without quantity → deduplicate to one."""
        storage.add_item("shopping", "lait")
        storage.add_item("shopping", "lait")

        data = storage.get_list("shopping")
        assert len(data) == 1

    def test_enrich_no_quantity_then_with_same_unit(self, storage):
        """
        First add without quantity and without unit, then again without unit
        but with a quantity → existing entry gets enriched (units_compatible:
        both None), still one item.
        """
        storage.add_item("shopping", "lait")
        storage.add_item("shopping", "lait", quantity=2)  # unit=None on both sides

        data = storage.get_list("shopping")
        assert len(data) == 1
        assert data[0]["quantity"] == 2
        assert data[0]["unit"] is None

    def test_no_enrich_when_unit_changes(self, storage):
        """
        Existing entry has no unit; new entry adds a unit → units_compatible
        is False (None != 'l'), so the entries are NOT merged.
        """
        storage.add_item("shopping", "lait")
        storage.add_item("shopping", "lait", quantity=2, unit="l")

        data = storage.get_list("shopping")
        assert len(data) == 2

    def test_different_items_not_merged(self, storage):
        storage.add_item("shopping", "lait")
        storage.add_item("shopping", "beurre")

        data = storage.get_list("shopping")
        assert len(data) == 2


# ---------------------------------------------------------------------------
# rename_item
# ---------------------------------------------------------------------------

class TestRenameItem:

    def test_rename_shopping_parses_quantity_and_unit(self, storage):
        """rename to '1 l whiskey' → text='whiskey', qty=1, unit='l'"""
        storage.add_item("shopping", "whisky", quantity=None)

        data = storage.get_list("shopping")
        item_id = data[0]["id"]

        result = storage.rename_item("shopping", item_id, "1 l whiskey")
        assert result is True

        data = storage.get_list("shopping")
        assert data[0]["text"] == "whiskey"
        assert data[0]["quantity"] == 1
        assert data[0]["unit"] == "l"

    def test_rename_does_not_store_synonym(self, storage):
        """
        Renaming a shopping item must NOT write anything into
        learning_synonyms.
        """
        storage.add_item("shopping", "pomme", quantity=None)
        data = storage.get_list("shopping")
        item_id = data[0]["id"]

        import app.database as _db
        conn = _db.get_db()
        syns_before = conn.execute(
            "SELECT COUNT(*) FROM learning_synonyms"
        ).fetchone()[0]
        conn.close()

        storage.rename_item("shopping", item_id, "pommes")

        conn = _db.get_db()
        syns_after = conn.execute(
            "SELECT COUNT(*) FROM learning_synonyms"
        ).fetchone()[0]
        conn.close()

        assert syns_before == syns_after

    def test_rename_todo_item(self, storage):
        storage.add_item("todo", "appeler le plombier")

        data = storage.get_list("todo")
        item_id = data[0]["id"]

        result = storage.rename_item("todo", item_id, "appeler le médecin")
        assert result is True

        data = storage.get_list("todo")
        assert data[0]["text"] == "appeler le médecin"

    def test_rename_nonexistent_id_returns_false(self, storage):
        result = storage.rename_item("todo", "nonexistent-id", "quelque chose")
        assert result is False


# ---------------------------------------------------------------------------
# delete_item
# ---------------------------------------------------------------------------

class TestDeleteItem:

    def test_delete_existing(self, storage):
        storage.add_item("todo", "appeler le plombier")

        data = storage.get_list("todo")
        item_id = data[0]["id"]

        result = storage.delete_item("todo", item_id)
        assert result is True

        data = storage.get_list("todo")
        assert len(data) == 0

    def test_delete_nonexistent_returns_false(self, storage):
        result = storage.delete_item("todo", "no-such-id")
        assert result is False


# ---------------------------------------------------------------------------
# update_item_done
# ---------------------------------------------------------------------------

class TestUpdateItemDone:

    def test_toggle_done_true(self, storage):
        storage.add_item("todo", "appeler le plombier")

        data = storage.get_list("todo")
        item_id = data[0]["id"]

        result = storage.update_item_done("todo", item_id, True)
        assert result is True

        data = storage.get_list("todo")
        assert data[0]["done"] is True

    def test_toggle_done_false(self, storage):
        storage.add_item("todo", "appeler le plombier")

        data = storage.get_list("todo")
        item_id = data[0]["id"]

        storage.update_item_done("todo", item_id, True)
        storage.update_item_done("todo", item_id, False)

        data = storage.get_list("todo")
        assert data[0]["done"] is False

    def test_update_done_nonexistent(self, storage):
        result = storage.update_item_done("todo", "no-id", True)
        assert result is False


# ---------------------------------------------------------------------------
# update_shopping_item
# ---------------------------------------------------------------------------

class TestUpdateShoppingItem:

    def test_update_text_quantity_unit(self, storage):
        storage.add_item("shopping", "poires", quantity=5)

        data = storage.get_list("shopping")
        item_id = data[0]["id"]

        result = storage.update_shopping_item(
            item_id=item_id,
            text="poires",
            quantity=10,
            unit=None,
            category="fruits",
        )
        assert result is True

        data = storage.get_list("shopping")
        assert data[0]["quantity"] == 10
        assert data[0]["text"] == "poires"
        assert data[0]["category"] == "fruits"

    def test_update_invalid_text_returns_false(self, storage):
        storage.add_item("shopping", "poires", quantity=5)

        data = storage.get_list("shopping")
        item_id = data[0]["id"]

        result = storage.update_shopping_item(item_id=item_id, text="")
        assert result is False
