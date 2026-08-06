from decimal import Decimal

import pytest

from src.utils.money import from_minor_units, to_minor_units


@pytest.mark.parametrize(
    ("major", "minor"),
    [
        ("0", 0),
        ("12.99", 1299),
        (Decimal("-4.25"), -425),
        (7, 700),
        ("1.005", 101),
    ],
)
#: Checks that pounds are correctly converted into pennies, such as £12.99 becoming 1299
def test_to_minor_units(major: Decimal | str | int, minor: int) -> None:
    assert to_minor_units(major) == minor


@pytest.mark.parametrize(
    ("minor", "major"),
    [(0, Decimal("0.00")), (1299, Decimal("12.99")), (-425, Decimal("-4.25"))],
)

#Checks that pennies are correctly converted back into pounds
def test_from_minor_units(minor: int, major: Decimal) -> None:
    assert from_minor_units(minor) == major


@pytest.mark.parametrize("invalid_amount", ["not-money", "NaN", "Infinity"])
#Ensures invalid amounts such as "not-money", NaN, and infinity are rejected.
def test_to_minor_units_rejects_invalid_values(invalid_amount: str) -> None:
    with pytest.raises(ValueError):
        to_minor_units(invalid_amount)

#Ensures True and False cannot accidentally be treated as money.
def test_money_helpers_reject_booleans() -> None:
    with pytest.raises(TypeError):
        to_minor_units(True)

    with pytest.raises(TypeError):
        from_minor_units(False)
