"""
Unit conversion utilities for shopping list quantity merging.

Base units:
  - Weight family: g (grams)
  - Volume family: ml (milliliters)

Unitless quantities (None) are treated as their own compatible "family".
"""

from __future__ import annotations

# Maps unit string → (family, factor_to_base)
UNIT_TO_BASE: dict[str, tuple[str, float]] = {
    "g":  ("weight", 1),
    "kg": ("weight", 1000),
    "ml": ("volume", 1),
    "cl": ("volume", 10),
    "l":  ("volume", 1000),
}


def units_are_compatible(unit_a: str | None, unit_b: str | None) -> bool:
    """Return True if unit_a and unit_b can be converted into each other.

    - None + None  → compatible (unitless)
    - None + unit  → incompatible
    - unit + None  → incompatible
    - same unit    → compatible
    - same family  → compatible (e.g. g and kg)
    - diff family  → incompatible (e.g. kg and l)
    - unknown unit → compatible only if strictly equal
    """
    if unit_a is None and unit_b is None:
        return True
    if unit_a is None or unit_b is None:
        return False
    if unit_a == unit_b:
        return True

    info_a = UNIT_TO_BASE.get(unit_a)
    info_b = UNIT_TO_BASE.get(unit_b)

    if info_a is None or info_b is None:
        # Unknown units: only equal units are compatible (handled above)
        return False

    return info_a[0] == info_b[0]


def to_base(quantity: float | int, unit: str) -> tuple[float, str]:
    """Convert quantity to the base unit of its family.

    Returns (base_quantity, family).
    Raises ValueError if unit is unknown.
    """
    info = UNIT_TO_BASE.get(unit)
    if info is None:
        raise ValueError(f"Unknown unit: {unit!r}")

    family, factor = info
    return quantity * factor, family


def from_base(base_quantity: float, family: str) -> tuple[float | int, str]:
    """Convert a base quantity to the most readable unit in its family.

    Weight:
      >= 1000 g → kg
      < 1000 g  → g

    Volume:
      >= 1000 ml → l
      >= 100 ml  → cl
      < 100 ml   → ml

    The result is an int if it is a whole number, a float otherwise.
    Rounded to 4 decimal places to avoid floating-point noise.
    """
    if family == "weight":
        if base_quantity >= 1000:
            value = round(base_quantity / 1000, 4)
            unit = "kg"
        else:
            value = round(base_quantity, 4)
            unit = "g"

    elif family == "volume":
        if base_quantity >= 1000:
            value = round(base_quantity / 1000, 4)
            unit = "l"
        elif base_quantity >= 100:
            value = round(base_quantity / 10, 4)
            unit = "cl"
        else:
            value = round(base_quantity, 4)
            unit = "ml"

    else:
        raise ValueError(f"Unknown family: {family!r}")

    # Return int when the value is whole (e.g. 2.0 → 2)
    if value == int(value):
        value = int(value)

    return value, unit


def merge_quantities(
    qty_a: float | int,
    unit_a: str | None,
    qty_b: float | int,
    unit_b: str | None,
) -> tuple[float | int, str | None] | None:
    """Add two quantities, handling unit conversion.

    Cases:
      - Both units None:       direct addition, unit stays None
      - Identical units:       direct addition, unit unchanged
      - Compatible units:      convert both to base, add, convert back
      - Incompatible units:    return None (cannot merge)

    Returns (quantity, unit) or None if incompatible.
    """
    # Both unitless
    if unit_a is None and unit_b is None:
        total = qty_a + qty_b
        total = round(total, 4)
        if total == int(total):
            total = int(total)
        return total, None

    # One has a unit, the other doesn't
    if unit_a is None or unit_b is None:
        return None

    # Identical units — direct addition (no conversion needed)
    if unit_a == unit_b:
        total = qty_a + qty_b
        total = round(total, 4)
        if total == int(total):
            total = int(total)
        return total, unit_a

    # Check compatibility via family
    info_a = UNIT_TO_BASE.get(unit_a)
    info_b = UNIT_TO_BASE.get(unit_b)

    if info_a is None or info_b is None:
        return None

    family_a, _ = info_a
    family_b, _ = info_b

    if family_a != family_b:
        return None

    # Compatible: convert to base, add, convert back
    base_a, family = to_base(qty_a, unit_a)
    base_b, _      = to_base(qty_b, unit_b)
    total_base = base_a + base_b

    return from_base(total_base, family)
