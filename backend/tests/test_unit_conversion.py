"""
Tests for app/unit_conversion.py:
  - units_are_compatible
  - to_base
  - from_base
  - merge_quantities
  - Integration: add_item cross-unit merging in storage
"""
import pytest
from unittest.mock import patch

from app.unit_conversion import (
    units_are_compatible,
    to_base,
    from_base,
    merge_quantities,
)


# ---------------------------------------------------------------------------
# units_are_compatible
# ---------------------------------------------------------------------------

class TestUnitsAreCompatible:

    def test_both_none(self):
        assert units_are_compatible(None, None) is True

    def test_one_none_left(self):
        assert units_are_compatible(None, "kg") is False

    def test_one_none_right(self):
        assert units_are_compatible("kg", None) is False

    def test_same_unit_g(self):
        assert units_are_compatible("g", "g") is True

    def test_same_unit_kg(self):
        assert units_are_compatible("kg", "kg") is True

    def test_same_unit_l(self):
        assert units_are_compatible("l", "l") is True

    def test_same_unit_ml(self):
        assert units_are_compatible("ml", "ml") is True

    def test_same_unit_cl(self):
        assert units_are_compatible("cl", "cl") is True

    def test_weight_g_kg(self):
        assert units_are_compatible("g", "kg") is True

    def test_weight_kg_g(self):
        assert units_are_compatible("kg", "g") is True

    def test_volume_ml_cl(self):
        assert units_are_compatible("ml", "cl") is True

    def test_volume_cl_l(self):
        assert units_are_compatible("cl", "l") is True

    def test_volume_ml_l(self):
        assert units_are_compatible("ml", "l") is True

    def test_cross_family_kg_l(self):
        assert units_are_compatible("kg", "l") is False

    def test_cross_family_g_ml(self):
        assert units_are_compatible("g", "ml") is False

    def test_cross_family_kg_ml(self):
        assert units_are_compatible("kg", "ml") is False

    def test_unknown_units_not_equal(self):
        assert units_are_compatible("boite", "paquet") is False

    def test_unknown_units_equal(self):
        # Same unknown unit → compatible (same string)
        assert units_are_compatible("boite", "boite") is True

    def test_unknown_vs_known(self):
        assert units_are_compatible("boite", "kg") is False


# ---------------------------------------------------------------------------
# to_base
# ---------------------------------------------------------------------------

class TestToBase:

    def test_grams(self):
        qty, family = to_base(500, "g")
        assert qty == 500
        assert family == "weight"

    def test_kilograms(self):
        qty, family = to_base(1, "kg")
        assert qty == 1000
        assert family == "weight"

    def test_kilograms_decimal(self):
        qty, family = to_base(1.5, "kg")
        assert qty == 1500
        assert family == "weight"

    def test_milliliters(self):
        qty, family = to_base(500, "ml")
        assert qty == 500
        assert family == "volume"

    def test_centiliters(self):
        qty, family = to_base(50, "cl")
        assert qty == 500
        assert family == "volume"

    def test_liters(self):
        qty, family = to_base(1, "l")
        assert qty == 1000
        assert family == "volume"

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown unit"):
            to_base(1, "boite")


# ---------------------------------------------------------------------------
# from_base
# ---------------------------------------------------------------------------

class TestFromBase:

    # Weight
    def test_weight_grams_small(self):
        qty, unit = from_base(500, "weight")
        assert qty == 500
        assert unit == "g"

    def test_weight_exactly_1000g_becomes_kg(self):
        qty, unit = from_base(1000, "weight")
        assert qty == 1
        assert unit == "kg"

    def test_weight_1500g_becomes_1_5kg(self):
        qty, unit = from_base(1500, "weight")
        assert qty == 1.5
        assert unit == "kg"

    def test_weight_2000g_becomes_2kg_int(self):
        qty, unit = from_base(2000, "weight")
        assert qty == 2
        assert isinstance(qty, int)
        assert unit == "kg"

    def test_weight_999g_stays_g(self):
        qty, unit = from_base(999, "weight")
        assert qty == 999
        assert unit == "g"

    # Volume
    def test_volume_ml_small(self):
        qty, unit = from_base(50, "volume")
        assert qty == 50
        assert unit == "ml"

    def test_volume_100ml_becomes_cl(self):
        qty, unit = from_base(100, "volume")
        assert qty == 10
        assert unit == "cl"

    def test_volume_500ml_becomes_cl(self):
        qty, unit = from_base(500, "volume")
        assert qty == 50
        assert unit == "cl"

    def test_volume_1000ml_becomes_l(self):
        qty, unit = from_base(1000, "volume")
        assert qty == 1
        assert isinstance(qty, int)
        assert unit == "l"

    def test_volume_1500ml_becomes_1_5l(self):
        qty, unit = from_base(1500, "volume")
        assert qty == 1.5
        assert unit == "l"

    def test_unknown_family_raises(self):
        with pytest.raises(ValueError, match="Unknown family"):
            from_base(100, "pressure")

    # Integer result
    def test_result_is_int_when_whole(self):
        qty, _ = from_base(2000, "weight")
        assert isinstance(qty, int), f"Expected int, got {type(qty)}"

    def test_result_is_float_when_fractional(self):
        qty, _ = from_base(1500, "weight")
        assert isinstance(qty, float), f"Expected float, got {type(qty)}"


# ---------------------------------------------------------------------------
# merge_quantities
# ---------------------------------------------------------------------------

class TestMergeQuantities:

    def test_both_no_unit(self):
        result = merge_quantities(3, None, 2, None)
        assert result == (5, None)

    def test_both_no_unit_result_int(self):
        qty, unit = merge_quantities(3, None, 2, None)
        assert isinstance(qty, int)

    def test_same_unit_kg(self):
        result = merge_quantities(2, "kg", 3, "kg")
        assert result == (5, "kg")

    def test_same_unit_result_int(self):
        qty, unit = merge_quantities(2, "kg", 3, "kg")
        assert isinstance(qty, int)

    def test_500g_plus_1kg_gives_1_5kg(self):
        qty, unit = merge_quantities(500, "g", 1, "kg")
        assert unit == "kg"
        assert qty == 1.5

    def test_1kg_plus_500g_gives_1_5kg(self):
        qty, unit = merge_quantities(1, "kg", 500, "g")
        assert unit == "kg"
        assert qty == 1.5

    def test_1000g_plus_1kg_gives_2kg_int(self):
        qty, unit = merge_quantities(1000, "g", 1, "kg")
        assert unit == "kg"
        assert qty == 2
        assert isinstance(qty, int)

    def test_500ml_plus_50cl_gives_1l(self):
        qty, unit = merge_quantities(500, "ml", 50, "cl")
        assert unit == "l"
        assert qty == 1
        assert isinstance(qty, int)

    def test_1l_plus_500ml_gives_1_5l(self):
        qty, unit = merge_quantities(1, "l", 500, "ml")
        assert unit == "l"
        assert qty == 1.5

    def test_incompatible_unit_vs_no_unit(self):
        result = merge_quantities(2, "kg", 3, None)
        assert result is None

    def test_no_unit_vs_incompatible_unit(self):
        result = merge_quantities(2, None, 3, "kg")
        assert result is None

    def test_incompatible_cross_family_kg_l(self):
        result = merge_quantities(2, "kg", 3, "l")
        assert result is None

    def test_incompatible_cross_family_g_ml(self):
        result = merge_quantities(500, "g", 500, "ml")
        assert result is None

    def test_no_floating_point_noise(self):
        """Result must not have excessive decimal places."""
        qty, unit = merge_quantities(500, "g", 1, "kg")
        # 1.5, not 1.5000000000001
        assert str(qty) == "1.5"


# ---------------------------------------------------------------------------
# Integration: add_item cross-unit merging in storage
# ---------------------------------------------------------------------------

@pytest.fixture
def storage(tmp_path):
    import app.database as _db
    import app.storage as _storage

    _db.set_db_path(str(tmp_path / "test_ambient.db"))
    _db.init_db()

    with (
        patch("app.cleaning.categorize_with_llm", return_value=None),
        patch("app.cleaning.get_learned_category", return_value=None),
        patch("app.cleaning.get_learned_synonym",  return_value=None),
    ):
        yield _storage

    import app.database as _db2
    from pathlib import Path
    _db2.set_db_path(str(Path(__file__).resolve().parent.parent / "data" / "ambient.db"))
    _db2.init_db()


class TestAddItemCrossUnitMerge:

    def test_500g_plus_1kg_merges_to_1_5kg(self, storage):
        """500 g farine + 1 kg farine → 1 item at 1.5 kg."""
        storage.add_item("shopping", "farine", quantity=500, unit="g")
        storage.add_item("shopping", "farine", quantity=1, unit="kg")

        data = storage.get_list("shopping")
        assert len(data) == 1, f"Expected 1 merged item, got {len(data)}"
        assert data[0]["unit"] == "kg"
        assert data[0]["quantity"] == 1.5

    def test_1kg_plus_500g_merges_to_1_5kg(self, storage):
        """Order reversed: 1 kg farine + 500 g farine → 1 item at 1.5 kg."""
        storage.add_item("shopping", "farine", quantity=1, unit="kg")
        storage.add_item("shopping", "farine", quantity=500, unit="g")

        data = storage.get_list("shopping")
        assert len(data) == 1, f"Expected 1 merged item, got {len(data)}"
        assert data[0]["unit"] == "kg"
        assert data[0]["quantity"] == 1.5

    def test_2000g_plus_1kg_merges_to_3kg_int(self, storage):
        """2000 g + 1 kg → 3 kg (integer result)."""
        storage.add_item("shopping", "sucre", quantity=2000, unit="g")
        storage.add_item("shopping", "sucre", quantity=1, unit="kg")

        data = storage.get_list("shopping")
        assert len(data) == 1
        assert data[0]["unit"] == "kg"
        assert data[0]["quantity"] == 3

    def test_500ml_plus_50cl_merges_to_1l(self, storage):
        """500 ml lait + 50 cl lait → 1 l."""
        storage.add_item("shopping", "lait", quantity=500, unit="ml")
        storage.add_item("shopping", "lait", quantity=50, unit="cl")

        data = storage.get_list("shopping")
        assert len(data) == 1, f"Expected 1 merged item, got {len(data)}"
        assert data[0]["unit"] == "l"
        assert data[0]["quantity"] == 1

    def test_kg_and_no_unit_not_merged(self, storage):
        """2 kg pommes + 3 pommes (no unit) → 2 separate items."""
        storage.add_item("shopping", "pommes", quantity=2, unit="kg")
        storage.add_item("shopping", "pommes", quantity=3, unit=None)

        data = storage.get_list("shopping")
        assert len(data) == 2, "kg vs no-unit must NOT be merged"

    def test_kg_and_l_not_merged(self, storage):
        """2 kg chose + 3 l chose → 2 separate items (incompatible families)."""
        storage.add_item("shopping", "chose", quantity=2, unit="kg")
        storage.add_item("shopping", "chose", quantity=3, unit="l")

        data = storage.get_list("shopping")
        assert len(data) == 2, "weight vs volume must NOT be merged"
